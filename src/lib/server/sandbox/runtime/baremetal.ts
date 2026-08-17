/**
 * Baremetal runtime — runs user code directly on the host.
 *
 * Two paths, same observable behaviour:
 *
 *   warm  — a pooled `run_host.py` process that already imported torch is
 *           handed the script path over stdin. Skips interpreter startup,
 *           uv resolution, the torch import and CUDA init. One run per host;
 *           the namespace is still fresh, so grading semantics are unchanged.
 *           See runtime/pool.ts for why it's one-shot.
 *   direct — the original `uv run python <tmpfile>` spawn. Used whenever no
 *           host is warm (first visit, cold cache, pooling disabled), and
 *           it schedules a warm-up afterwards so the next Run is fast.
 *
 * Both stream stdout/stderr into the registry as they arrive so the SSE
 * live tail works, and both resolve to a RunOutcome that drives the session
 * lifecycle in `sandbox/index.ts`.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { writeFileSync, unlinkSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import * as registry from '../registry.js';
import type { LogChunk, ResourceLimits, SessionRecord } from '../types.js';
import * as pool from './pool.js';
import { childEnv, requirementsUsesTorchIndex, resolveTorchIndex, uvRunArgs } from './pyenv.js';
import { ensureVenv, venvSpecFor } from './venvs.js';

const IS_WINDOWS = process.platform === 'win32';

// ── Tree kill (copied from executor.ts so the sandbox is self-contained) ──

function treeKill(child: ChildProcess): void {
  if (!child.pid || child.exitCode !== null) return;
  if (IS_WINDOWS) {
    try {
      spawn('taskkill', ['/F', '/T', '/PID', String(child.pid)], {
        stdio: 'ignore',
        windowsHide: true
      });
    } catch {
      try { child.kill('SIGKILL'); } catch { /* ignore */ }
    }
  } else {
    try {
      process.kill(-child.pid, 'SIGKILL');
    } catch {
      try { child.kill('SIGKILL'); } catch { /* ignore */ }
    }
  }
}

// ── Public surface ────────────────────────────────────────────────────────

export interface RunOutcome {
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
  /** Total stdout/stderr byte counts (cumulative, for the row). */
  stdoutBytes: number;
  stderrBytes: number;
  /** First MAX_CAPTURE_BYTES of stdout — used for submit grading. */
  capturedStdout: string;
  /** First MAX_CAPTURE_BYTES of stderr — surfaced if exit != 0. */
  capturedStderr: string;
  errorMessage?: string;
}

/**
 * Cap on captured stdout/stderr passed back to the orchestrator. 1 MB is
 * comfortably more than any reasonable expected_output, and prevents a
 * runaway process from ballooning Node's heap with multi-GB log dumps.
 */
const MAX_CAPTURE_BYTES = 1_048_576;

export interface BaremetalRunOpts {
  record: SessionRecord;
  code: string;
  requirementsPath?: string;
  resources: ResourceLimits;
}

/**
 * Execute the session. Streams output via `registry.publish` so SSE
 * subscribers see it live. Resolves to the final outcome (no throws —
 * errors are mapped to a status chunk + error message).
 */
export async function runBaremetal(opts: BaremetalRunOpts): Promise<RunOutcome> {
  const { record, code, requirementsPath } = opts;

  if (record.language === 'python') {
    return runPython(record, code, requirementsPath, opts.resources);
  }
  if (record.language === 'cpp') {
    return runCpp(record, code, opts.resources);
  }
  registry.publish(record.id, {
    kind: 'stderr',
    data: `Unsupported language: ${record.language}\n`
  });
  return {
    exitCode: 1,
    timedOut: false,
    durationMs: 0,
    stdoutBytes: 0,
    stderrBytes: 0,
    capturedStdout: '',
    capturedStderr: `Unsupported language: ${record.language}\n`,
    errorMessage: `Unsupported language: ${record.language}`
  };
}

// ── Internal language runners ─────────────────────────────────────────────

/** Progress note on the session's stderr stream. Mirrors the docker runtime. */
function note(id: string, message: string): void {
  registry.publish(id, { kind: 'stderr', data: `[sandbox] ${message}\n` });
}

async function runPython(
  record: SessionRecord,
  code: string,
  requirementsPath: string | undefined,
  resources: ResourceLimits
): Promise<RunOutcome> {
  const tmpFile = path.join(tmpdir(), `jeff-${record.id}.py`);
  writeFileSync(tmpFile, code, 'utf-8');
  const spec = pool.specFor(requirementsPath);

  try {
    const host = pool.isPoolable(spec) ? pool.acquire(spec) : null;

    if (host) {
      note(record.id, `warm process — ${spec.prewarm.join(', ')} already imported`);
      try {
        return await streamProcess(record, host.proc, resources.timeoutMs, () => {
          host.dispatch(tmpFile);
        });
      } finally {
        host.release();
        pool.scheduleWarm(spec);
      }
    }

    // Prefer the module's persistent venv: no resolution on the hot path,
    // and it sidesteps the ephemeral-environment install failures uv hits on
    // Windows (see runtime/venvs.ts). Falls back to `uv run` if it can't be
    // built, so a broken venv never blocks a run outright.
    const venvPython = requirementsPath
      ? await ensureVenv(venvSpecFor(requirementsPath), (msg) => note(record.id, msg))
      : null;

    let cmd: string;
    let args: string[];
    if (venvPython) {
      cmd = venvPython;
      args = [tmpFile];
    } else {
      if (requirementsPath) {
        note(record.id, 'resolving python environment (first run for this module is slower)…');
      }
      const torchIndex = requirementsUsesTorchIndex(requirementsPath)
        ? await resolveTorchIndex()
        : undefined;
      cmd = 'uv';
      args = uvRunArgs({ script: tmpFile, requirementsPath, torchIndex });
    }

    try {
      return await spawnStreaming(record, cmd, args, resources.timeoutMs);
    } finally {
      // Warm a host for next time. Deliberately after the run, never during:
      // two concurrent uv invocations contend on the same cache.
      pool.scheduleWarm(spec);
    }
  } finally {
    tryUnlink(tmpFile);
  }
}

async function runCpp(
  record: SessionRecord,
  code: string,
  resources: ResourceLimits
): Promise<RunOutcome> {
  const id = randomUUID();
  const tmpSrc = path.join(tmpdir(), `${id}.cpp`);
  const tmpBin = path.join(tmpdir(), IS_WINDOWS ? `${id}.exe` : id);
  writeFileSync(tmpSrc, code, 'utf-8');

  try {
    // Compile (we still surface compile errors live via the same stream).
    const compileOutcome = await spawnStreaming(
      record,
      'g++',
      ['-std=c++17', '-O2', '-o', tmpBin, tmpSrc],
      Math.min(resources.timeoutMs, 30_000)
    );
    if (compileOutcome.exitCode !== 0 || compileOutcome.errorMessage) {
      return compileOutcome;
    }
    const runOutcome = await spawnStreaming(record, tmpBin, [], resources.timeoutMs);
    return {
      ...runOutcome,
      durationMs: compileOutcome.durationMs + runOutcome.durationMs,
      stdoutBytes: compileOutcome.stdoutBytes + runOutcome.stdoutBytes,
      stderrBytes: compileOutcome.stderrBytes + runOutcome.stderrBytes,
      // Compile output isn't part of the program's logical stdout, so we
      // leave capturedStdout untouched and only forward compile-stage
      // stderr if the run-stage produced nothing on its own.
      capturedStdout: runOutcome.capturedStdout,
      capturedStderr: runOutcome.capturedStderr || compileOutcome.capturedStderr
    };
  } finally {
    tryUnlink(tmpSrc);
    tryUnlink(tmpBin);
  }
}

// ── Core streaming spawn ──────────────────────────────────────────────────

function failedOutcome(errorMessage: string, durationMs = 0): RunOutcome {
  return {
    exitCode: null,
    timedOut: false,
    durationMs,
    stdoutBytes: 0,
    stderrBytes: errorMessage.length,
    capturedStdout: '',
    capturedStderr: errorMessage,
    errorMessage
  };
}

/**
 * Spawn a child and stream it. Thin wrapper around `streamProcess` for the
 * direct path.
 */
function spawnStreaming(
  record: SessionRecord,
  cmd: string,
  args: string[],
  timeoutMs: number
): Promise<RunOutcome> {
  const entry = registry.getEntry(record.id);
  if (!entry) {
    return Promise.resolve(failedOutcome('Session record missing from registry'));
  }
  if (entry.abort.signal.aborted) {
    return Promise.resolve(failedOutcome('Aborted before start'));
  }

  let proc: ChildProcess;
  try {
    proc = spawn(cmd, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: !IS_WINDOWS,
      windowsHide: true,
      env: childEnv()
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    registry.publish(record.id, { kind: 'stderr', data: `Failed to spawn: ${msg}\n` });
    return Promise.resolve(failedOutcome(msg));
  }

  return streamProcess(record, proc, timeoutMs);
}

/**
 * Stream an already-running child's stdout/stderr into the registry, kill it
 * when the session's abort controller fires or the timeout elapses, and
 * resolve with the final byte counts and exit code.
 *
 * `onAttached` runs once the stream handlers are wired — the pool uses it to
 * hand the script path to a warm host, so no output can be emitted before
 * anyone is listening.
 *
 * Importantly: this does NOT throw. Cancellation is signalled in the
 * returned outcome (exitCode=null, errorMessage describes why).
 */
function streamProcess(
  record: SessionRecord,
  proc: ChildProcess,
  timeoutMs: number,
  onAttached?: () => void
): Promise<RunOutcome> {
  return new Promise((resolve) => {
    const entry = registry.getEntry(record.id);
    if (!entry) {
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      resolve(failedOutcome('Session record missing from registry'));
      return;
    }
    if (entry.abort.signal.aborted) {
      treeKill(proc);
      resolve(failedOutcome('Aborted before start'));
      return;
    }

    const start = Date.now();
    let stdoutBytes = 0;
    let stderrBytes = 0;
    let capturedStdout = '';
    let capturedStderr = '';
    let timedOut = false;
    let aborted = false;
    let killedByCaller = false;

    entry.proc = proc;
    registry.patchRecord(record.id, { hostPid: proc.pid ?? null });

    proc.stdout?.on('data', (chunk: Buffer) => {
      stdoutBytes += chunk.length;
      const data = chunk.toString();
      if (capturedStdout.length < MAX_CAPTURE_BYTES) {
        capturedStdout += data.slice(0, MAX_CAPTURE_BYTES - capturedStdout.length);
      }
      const log: LogChunk = { kind: 'stdout', data };
      registry.publish(record.id, log);
    });
    proc.stderr?.on('data', (chunk: Buffer) => {
      stderrBytes += chunk.length;
      const data = chunk.toString();
      if (capturedStderr.length < MAX_CAPTURE_BYTES) {
        capturedStderr += data.slice(0, MAX_CAPTURE_BYTES - capturedStderr.length);
      }
      const log: LogChunk = { kind: 'stderr', data };
      registry.publish(record.id, log);
    });
    // A pooled host's streams were parked on acquire; the listeners above
    // resume flow, but be explicit so this doesn't depend on stream internals.
    proc.stdout?.resume();
    proc.stderr?.resume();

    const timer = setTimeout(() => {
      timedOut = true;
      killedByCaller = true;
      treeKill(proc);
    }, timeoutMs);

    const onAbort = () => {
      aborted = true;
      killedByCaller = true;
      treeKill(proc);
    };
    entry.abort.signal.addEventListener('abort', onAbort, { once: true });

    const finish = (exitCode: number | null, errorMessage?: string) => {
      clearTimeout(timer);
      entry.abort.signal.removeEventListener('abort', onAbort);
      resolve({
        exitCode,
        timedOut,
        durationMs: Date.now() - start,
        stdoutBytes,
        stderrBytes,
        capturedStdout,
        capturedStderr,
        errorMessage: errorMessage ?? (
          timedOut ? 'Timed out' :
          aborted ? 'Cancelled' :
          undefined
        )
      });
    };

    proc.on('close', (exitCode) => finish(killedByCaller ? null : exitCode));
    proc.on('error', (err) => finish(null, err.message));

    onAttached?.();
  });
}

function tryUnlink(filePath: string): void {
  try {
    if (existsSync(filePath)) unlinkSync(filePath);
  } catch {
    // best effort
  }
}
