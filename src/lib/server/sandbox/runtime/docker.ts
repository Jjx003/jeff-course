/**
 * Docker runtime — runs a session in a short-lived `docker run --rm` container.
 *
 * Phase 3 implementation. See the brief's "Architecture → Docker runtime"
 * section. Highlights:
 *
 *   - Each session = one container. We pass `--name jeff-course-<id>` so we
 *     can `docker stop` / `docker kill` it by name without tracking the pid.
 *   - Containers are labelled `jeff-course=1 session-id=<id>` so the
 *     boot-time zombie reaper can find and remove them after a crash.
 *   - User code is written to a host tmp file and bind-mounted read-only at
 *     `/workspace/user.py` (or `.cpp`).
 *   - The uv / pip / huggingface caches are bind-mounted to `data/cache/*`
 *     so the second run reuses downloaded wheels and model weights —
 *     this is the headline UX win for the protein-folding track.
 *   - `--network bridge` always. Container runs resolve their requirement
 *     set with uv on every start and most ML modules pull weights from the
 *     Hub, so cutting the network breaks the common case rather than the
 *     rare one. (An earlier version of this comment claimed none-by-default;
 *     the code never did that.)
 *   - Cancellation: `docker stop --time=2 <name>` then `docker kill -s KILL`
 *     if the container is still alive after the grace window.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { mkdirSync, writeFileSync, unlinkSync } from 'node:fs';
import path from 'node:path';

import * as registry from '../registry.js';
import type { LogChunk, ResourceLimits, SessionRecord } from '../types.js';
import type { Problem } from '$lib/types/course.js';
import {
  PYPI_EXTRA_INDEX,
  PYTORCH_CPU_INDEX,
  PYTORCH_CUDA_INDEX,
  requirementsUsesTorchIndex
} from './pyenv.js';

const IS_WINDOWS = process.platform === 'win32';

// ── Image tags ────────────────────────────────────────────────────────────
//
// Bump the version suffix whenever you change the corresponding Dockerfile
// in infra/docker/. `images.ts` will rebuild on next session if the tag
// isn't found locally.

export const IMAGE_CPP = 'jeff-course/cpp:1';
export const IMAGE_PYTHON_CUDA = 'jeff-course/python-cuda:1';
export const IMAGE_PYTHON_CPU = 'jeff-course/python:1';

// ── Cache directories on the host ────────────────────────────────────────
//
// uv and pip caches use named Docker volumes (not bind mounts) so they
// live inside the Docker/WSL2 VM filesystem. Bind-mounting Windows
// directories for these caches causes "Permission denied" on atomic
// cross-directory renames that uv performs when populating its cache
// (DrvFs/9p does not support that operation). Named volumes are opaque
// to the Windows host but work correctly and persist across runs.
//
// Huggingface stays as a bind mount because we inspect it from the host
// to decide whether to allow network access (cold-cache check).

const UV_CACHE_VOLUME  = 'jeff-course-uv-cache';
const PIP_CACHE_VOLUME = 'jeff-course-pip-cache';

function ensureCacheDirs(): { huggingface: string } {
  const root = path.join(process.cwd(), 'data', 'cache');
  const huggingface = path.join(root, 'huggingface');
  mkdirSync(huggingface, { recursive: true });
  return { huggingface };
}

// ── GPU args ──────────────────────────────────────────────────────────────

function gpuArgs(gpu: ResourceLimits['gpu']): string[] {
  if (gpu === 'all') return ['--gpus', 'all'];
  if (typeof gpu === 'object' && gpu.device !== undefined) {
    return ['--gpus', `device=${gpu.device}`];
  }
  return [];
}

// ── Public surface (mirrors RunOutcome from baremetal) ───────────────────

export interface DockerRunOpts {
  record: SessionRecord;
  code: string;
  requirementsPath?: string;
  resources: ResourceLimits;
  problem: Problem;
}

export interface DockerOutcome {
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
  stdoutBytes: number;
  stderrBytes: number;
  capturedStdout: string;
  capturedStderr: string;
  errorMessage?: string;
}

const MAX_CAPTURE_BYTES = 1_048_576;

export async function runDocker(opts: DockerRunOpts): Promise<DockerOutcome> {
  const { record, code, requirementsPath, resources } = opts;
  const entry = registry.getEntry(record.id);
  if (!entry) {
    return baseFailure('Session record missing from registry');
  }
  if (entry.abort.signal.aborted) {
    return baseFailure('Aborted before start');
  }

  // Make sure the image we need exists. ensureImagePulled is a thin wrapper
  // around `docker image inspect` and the local build script.
  const { ensureImagePulled } = await import('../images.js');

  const isPython = record.language === 'python';
  // Only reach for the CUDA image when a GPU was actually requested. Picking
  // it for any module with a requirements.txt meant CPU runs built and kept
  // an nvidia/cuda base image to execute numpy.
  const wantsGpu = resources.gpu === 'all' || typeof resources.gpu === 'object';
  const image = isPython
    ? (wantsGpu ? IMAGE_PYTHON_CUDA : IMAGE_PYTHON_CPU)
    : IMAGE_CPP;

  try {
    await ensureImagePulled(image, (msg) => {
      registry.publish(record.id, { kind: 'stderr', data: `[sandbox] ${msg}\n` });
    });
  } catch (err) {
    return baseFailure(err instanceof Error ? err.message : String(err));
  }

  // Write the user code to a host tmp file we'll bind-mount.
  const workDir = path.join(process.cwd(), 'data', 'sandbox-work', record.id);
  mkdirSync(workDir, { recursive: true });
  const fileName = isPython ? 'user.py' : 'user.cpp';
  const hostSrc = path.join(workDir, fileName);
  writeFileSync(hostSrc, code, 'utf-8');

  const { huggingface } = ensureCacheDirs();

  const containerName = `jeff-course-${record.id}`;
  registry.patchRecord(record.id, { containerName });

  const args: string[] = [
    'run', '--rm',
    '--name', containerName,
    '--label', 'jeff-course=1',
    '--label', `session-id=${record.id}`,
    '--workdir', '/workspace',
    '--memory', `${resources.memoryMb}m`,
    '--cpus', String(resources.cpus),
    '--network', 'bridge',
    ...gpuArgs(resources.gpu),
    // Mounts
    '-v', `${hostSrc}:/workspace/${fileName}:ro`,
    ...(requirementsPath ? ['-v', `${requirementsPath}:/workspace/requirements.txt:ro`] : []),
    // Named volumes for uv/pip: avoids Windows bind-mount rename failures.
    '--mount', `type=volume,source=${UV_CACHE_VOLUME},target=/root/.cache/uv`,
    '--mount', `type=volume,source=${PIP_CACHE_VOLUME},target=/root/.cache/pip`,
    '-v', `${huggingface}:/root/.cache/huggingface`,
    '--tmpfs', '/tmp',
    image,
    ...entrypointArgs(record.language, !!requirementsPath, fileName, torchIndexForContainer(requirementsPath, wantsGpu))
  ];

  registry.publish(record.id, { kind: 'stderr', data: `[sandbox] docker run ${containerName}\n` });

  const outcome = await spawnStreaming(record, 'docker', args, resources.timeoutMs, containerName);

  // Best-effort cleanup of the host tmp file.
  try { unlinkSync(hostSrc); } catch { /* ignore */ }

  return outcome;
}

// ── Helpers ───────────────────────────────────────────────────────────────

/**
 * Which torch wheel index the container should resolve against.
 *
 * PyPI's default linux `torch` wheel is the CUDA build (~2.5 GB), which is
 * pure waste inside a CPU container. Mirrors what the baremetal path does
 * on the host — see runtime/pyenv.ts.
 */
function torchIndexForContainer(requirementsPath: string | undefined, wantsGpu: boolean): string | null {
  if (!requirementsUsesTorchIndex(requirementsPath)) return null;
  return wantsGpu ? PYTORCH_CUDA_INDEX : PYTORCH_CPU_INDEX;
}

function entrypointArgs(
  language: SessionRecord['language'],
  hasRequirements: boolean,
  fileName: string,
  torchIndex: string | null
): string[] {
  if (language === 'cpp') {
    // Two-step inline: compile + run. We tolerate the compile output going
    // to stderr; user-program stdout is what we grade against.
    return [
      'bash', '-lc',
      `g++ -std=c++17 -O2 -o /tmp/user /workspace/${fileName} && /tmp/user`
    ];
  }
  // python
  if (hasRequirements) {
    const indexFlags = torchIndex
      ? `--index-url ${torchIndex} --extra-index-url ${PYPI_EXTRA_INDEX} --index-strategy unsafe-best-match `
      : '';
    return [
      'bash', '-lc',
      `uv run --python 3.11 ${indexFlags}--with-requirements /workspace/requirements.txt python /workspace/${fileName}`
    ];
  }
  return ['bash', '-lc', `uv run python /workspace/${fileName}`];
}

function baseFailure(msg: string): DockerOutcome {
  return {
    exitCode: null,
    timedOut: false,
    durationMs: 0,
    stdoutBytes: 0,
    stderrBytes: msg.length,
    capturedStdout: '',
    capturedStderr: msg,
    errorMessage: msg
  };
}

/**
 * Spawn `docker run ...`, stream output, and kill the container on abort
 * or timeout. Returns a DockerOutcome shaped like the baremetal one so
 * the orchestrator can treat both identically.
 */
function spawnStreaming(
  record: SessionRecord,
  cmd: string,
  args: string[],
  timeoutMs: number,
  containerName: string
): Promise<DockerOutcome> {
  return new Promise((resolve) => {
    const entry = registry.getEntry(record.id);
    if (!entry) {
      resolve(baseFailure('Session record missing from registry'));
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
        windowsHide: true
      });
    } catch (err) {
      resolve(baseFailure(err instanceof Error ? err.message : String(err)));
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

    const stopContainer = async (force: boolean) => {
      const sub = spawn(
        'docker',
        force
          ? ['kill', '-s', 'KILL', containerName]
          : ['stop', '--time', '2', containerName],
        { stdio: 'ignore', windowsHide: true }
      );
      await new Promise<void>((r) => {
        sub.on('close', () => r());
        sub.on('error', () => r());
      });
    };

    const timer = setTimeout(() => {
      timedOut = true;
      killedByCaller = true;
      void stopContainer(false).then(() => stopContainer(true));
    }, timeoutMs);

    const onAbort = () => {
      aborted = true;
      killedByCaller = true;
      // Try graceful first. If the container ignores SIGTERM, hard kill.
      void stopContainer(false).then(async () => {
        await new Promise((r) => setTimeout(r, 2_100));
        await stopContainer(true);
      });
    };
    entry.abort.signal.addEventListener('abort', onAbort, { once: true });

    const finish = (exitCode: number | null, errorMessage?: string) => {
      clearTimeout(timer);
      entry.abort.signal.removeEventListener('abort', onAbort);
      resolve({
        exitCode: killedByCaller ? null : exitCode,
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

    proc.on('close', (exitCode) => finish(exitCode));
    proc.on('error', (err) => finish(null, err.message));
  });
}

// Suppress "unused" warning for IS_WINDOWS which we still want to surface
// in case future image-pulling logic needs platform branching. Marking as
// touch-only keeps tsc happy without a comment-disable.
void IS_WINDOWS;

// ── Boot-time zombie reap ─────────────────────────────────────────────────

const REAP_LIST_TIMEOUT_MS = 5_000;

interface SpawnTextResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
  error?: Error;
}

function spawnCaptureText(cmd: string, args: string[], timeoutMs: number): Promise<SpawnTextResult> {
  return new Promise((resolve) => {
    let settled = false;
    let stdout = '';
    let stderr = '';
    let proc: ChildProcess;
    try {
      proc = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
    } catch (err) {
      resolve({
        stdout: '',
        stderr: err instanceof Error ? err.message : String(err),
        exitCode: null,
        timedOut: false,
        error: err instanceof Error ? err : new Error(String(err))
      });
      return;
    }
    const timer = setTimeout(() => {
      if (settled) return;
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      settled = true;
      resolve({ stdout, stderr, exitCode: null, timedOut: true });
    }, timeoutMs);
    proc.stdout?.on('data', (b: Buffer) => { stdout += b.toString(); });
    proc.stderr?.on('data', (b: Buffer) => { stderr += b.toString(); });
    proc.on('error', (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode: null, timedOut: false, error: err });
    });
    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode: code, timedOut: false });
    });
  });
}

/**
 * Best-effort cleanup of any leftover jeff-course containers from a prior
 * crash. Looks for containers labelled `jeff-course` and force-removes them.
 *
 * Soft-fails when:
 *   - `docker` is not installed or not on PATH
 *   - docker daemon is not reachable (returns a non-zero exit code with
 *     "Cannot connect to the Docker daemon")
 *   - the listing call times out
 *
 * This function never throws. It's safe to call unconditionally from the
 * boot hook.
 */
export async function reapZombieContainers(): Promise<{ removed: string[]; reason?: string }> {
  const list = await spawnCaptureText(
    'docker',
    ['ps', '-a', '--filter', 'label=jeff-course', '--format', '{{.Names}}'],
    REAP_LIST_TIMEOUT_MS
  );

  if (list.error) {
    return { removed: [], reason: list.error.message };
  }
  if (list.timedOut) {
    return { removed: [], reason: 'docker ps timed out' };
  }
  if (list.exitCode !== 0) {
    const reason = list.stderr.trim().split('\n')[0] || `docker ps exited ${list.exitCode}`;
    return { removed: [], reason };
  }

  const names = list.stdout
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);

  if (names.length === 0) return { removed: [] };

  // `docker rm -f` accepts multiple names in a single invocation. We use a
  // generous (but bounded) timeout proportional to how many we have to
  // tear down, capped at 30 seconds.
  const rm = await spawnCaptureText(
    'docker',
    ['rm', '-f', ...names],
    Math.min(30_000, 5_000 + names.length * 1_000)
  );

  if (rm.exitCode !== 0) {
    return {
      removed: [],
      reason: rm.stderr.trim().split('\n')[0] || `docker rm exited ${rm.exitCode}`
    };
  }

  return { removed: names };
}
