/**
 * Baremetal runtime — spawns `uv run python` / `g++` + binary directly on
 * the host, exactly like the legacy `executor.ts` did. The behavior is
 * preserved (tree-kill, abort signal, BOM-tolerant requirements parsing,
 * dynamic torch index resolution) but reshaped so:
 *
 *   - stdout/stderr stream into the registry as they arrive (instead of
 *     being buffered until the process exits), enabling SSE live tail.
 *   - the wrapper returns a Promise<RunOutcome> that drives the session
 *     lifecycle in `sandbox/index.ts`.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { writeFileSync, unlinkSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import * as registry from '../registry.js';
import type { LogChunk, ResourceLimits, SessionRecord } from '../types.js';

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

// ── Torch index resolution (carry-over) ───────────────────────────────────

const PYTORCH_CPU_INDEX = 'https://download.pytorch.org/whl/cpu';
const PYTORCH_CUDA_INDEX = 'https://download.pytorch.org/whl/cu124';
const PYPI_EXTRA_INDEX = 'https://pypi.org/simple';
const TORCH_INDEX_URL = process.env.TORCH_INDEX_URL ?? null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
const torchIndexPromise: Promise<string> =
  g.__sandboxTorchIdx ?? (g.__sandboxTorchIdx = detectCudaIndex());

function detectCudaIndex(): Promise<string> {
  if (TORCH_INDEX_URL) return Promise.resolve(TORCH_INDEX_URL);
  return new Promise((resolve) => {
    let settled = false;
    const finish = (idx: string) => {
      if (settled) return;
      settled = true;
      resolve(idx);
    };
    const proc = spawn('nvidia-smi', ['--query-gpu=name', '--format=csv,noheader'], {
      stdio: ['ignore', 'pipe', 'ignore'],
      windowsHide: true
    });
    const timer = setTimeout(() => {
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      finish(PYTORCH_CPU_INDEX);
    }, 2_000);
    proc.on('close', (code) => {
      clearTimeout(timer);
      finish(code === 0 ? PYTORCH_CUDA_INDEX : PYTORCH_CPU_INDEX);
    });
    proc.on('error', () => {
      clearTimeout(timer);
      finish(PYTORCH_CPU_INDEX);
    });
  });
}

function requirementsUsesTorchIndex(reqPath: string): boolean {
  try {
    const content = readFileSync(reqPath, 'utf-8').replace(/^\uFEFF/, '');
    return /^\s*torch[>=<!,\s]/m.test(content);
  } catch {
    return false;
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

async function runPython(
  record: SessionRecord,
  code: string,
  requirementsPath: string | undefined,
  resources: ResourceLimits
): Promise<RunOutcome> {
  const tmpFile = path.join(tmpdir(), `jeff-${record.id}.py`);
  writeFileSync(tmpFile, code, 'utf-8');
  try {
    let args: string[];
    if (requirementsPath) {
      if (requirementsUsesTorchIndex(requirementsPath)) {
        const torchIndex = await torchIndexPromise;
        args = [
          'run', '--python', '3.11',
          '--index-url', torchIndex,
          '--extra-index-url', PYPI_EXTRA_INDEX,
          '--index-strategy', 'unsafe-best-match',
          '--with-requirements', requirementsPath,
          'python', tmpFile
        ];
      } else {
        args = ['run', '--python', '3.11', '--with-requirements', requirementsPath, 'python', tmpFile];
      }
    } else {
      args = ['run', 'python', tmpFile];
    }
    return await spawnStreaming(record, 'uv', args, resources.timeoutMs);
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

/**
 * Spawn a child, stream its stdout/stderr into the registry, kill it when
 * the session's abort controller fires or the timeout elapses, and resolve
 * with the final byte counts and exit code.
 *
 * Importantly: this does NOT throw. Cancellation is signalled in the
 * returned outcome (exitCode=null, errorMessage describes why).
 */
function spawnStreaming(
  record: SessionRecord,
  cmd: string,
  args: string[],
  timeoutMs: number
): Promise<RunOutcome> {
  return new Promise((resolve) => {
    const entry = registry.getEntry(record.id);
    if (!entry) {
      resolve({
        exitCode: null, timedOut: false, durationMs: 0,
        stdoutBytes: 0, stderrBytes: 0,
        capturedStdout: '', capturedStderr: '',
        errorMessage: 'Session record missing from registry'
      });
      return;
    }
    if (entry.abort.signal.aborted) {
      resolve({
        exitCode: null, timedOut: false, durationMs: 0,
        stdoutBytes: 0, stderrBytes: 0,
        capturedStdout: '', capturedStderr: '',
        errorMessage: 'Aborted before start'
      });
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

    let proc: ChildProcess;
    try {
      proc = spawn(cmd, args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: !IS_WINDOWS,
        windowsHide: true
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      registry.publish(record.id, { kind: 'stderr', data: `Failed to spawn: ${msg}\n` });
      resolve({
        exitCode: null, timedOut: false, durationMs: Date.now() - start,
        stdoutBytes: 0, stderrBytes: msg.length,
        capturedStdout: '', capturedStderr: msg,
        errorMessage: msg
      });
      return;
    }

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
  });
}

function tryUnlink(filePath: string): void {
  try {
    if (existsSync(filePath)) unlinkSync(filePath);
  } catch {
    // best effort
  }
}
