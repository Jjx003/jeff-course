/**
 * Persistent per-requirement-set virtualenvs.
 *
 * The original run path was `uv run --with-requirements <reqs> python <file>`,
 * which re-resolves the requirement set on every single Run and stages an
 * ephemeral environment under uv's build cache. Two problems with that:
 *
 *   1. Resolution is on the hot path. Every click pays for it.
 *   2. On Windows the ephemeral-environment path is fragile. On this
 *      machine it fails outright for any torch module:
 *        failed to remove directory `…/builds-v0/.tmpXXXX/Lib/site-packages/
 *        sympy-1.14.0.data`: The process cannot access the file because it is
 *        being used by another process. (os error 32)
 *      — a real-time scanner holding a handle on freshly extracted files
 *      while uv tries to clean up. `uv pip install` into a persistent venv
 *      installs the identical wheels without touching that path.
 *
 * So we materialize one venv per requirement set under `data/venvs/<key>`,
 * where the key is a hash of the requirements content: modules that declare
 * identical dependencies share one, and editing a requirements.txt yields a
 * new key rather than a stale environment.
 *
 * Everything here is best-effort. If uv is missing or an install fails, the
 * caller falls back to the original `uv run` invocation.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import {
  childEnv,
  requirementsKey,
  requirementsUsesTorchIndex,
  resolveTorchIndex,
  PYPI_EXTRA_INDEX
} from './pyenv.js';

const IS_WINDOWS = process.platform === 'win32';

/** Ready-marker filename inside a venv directory. */
const READY_MARKER = '.jeff-course-ready';

/** Ceiling on `uv venv` + `uv pip install` for one requirement set. */
const INSTALL_TIMEOUT_MS = 15 * 60_000;

export interface VenvSpec {
  key: string;
  requirementsPath?: string;
}

function venvRoot(): string {
  return path.join(process.cwd(), 'data', 'venvs');
}

function venvDir(key: string): string {
  return path.join(venvRoot(), key);
}

/** Interpreter path inside a venv, per platform layout. */
function venvPython(dir: string): string {
  return IS_WINDOWS
    ? path.join(dir, 'Scripts', 'python.exe')
    : path.join(dir, 'bin', 'python');
}

/**
 * Path to a ready interpreter for this key, or null. Synchronous and cheap —
 * safe to call on the hot path before deciding how to run.
 */
export function readyPython(key: string): string | null {
  const dir = venvDir(key);
  const marker = path.join(dir, READY_MARKER);
  if (!existsSync(marker)) return null;
  const python = venvPython(dir);
  if (!existsSync(python)) return null;
  try {
    // The marker records the key it was built for; a mismatch means the
    // directory was reused by hand and can't be trusted.
    return readFileSync(marker, 'utf-8').trim() === key ? python : null;
  } catch {
    return null;
  }
}

// ── Build ─────────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
const INFLIGHT: Map<string, Promise<string | null>> =
  g.__sandboxVenvInflight ?? (g.__sandboxVenvInflight = new Map<string, Promise<string | null>>());
const FAILED: Set<string> = g.__sandboxVenvFailed ?? (g.__sandboxVenvFailed = new Set<string>());

export type ProgressFn = (message: string) => void;

/**
 * Ensure a venv exists for `spec` and return its interpreter path, or null
 * when one can't be built (no requirements, uv missing, install failed).
 *
 * Concurrent callers for the same key share a single install.
 */
export function ensureVenv(spec: VenvSpec, onProgress?: ProgressFn): Promise<string | null> {
  if (!spec.requirementsPath) return Promise.resolve(null);

  const ready = readyPython(spec.key);
  if (ready) return Promise.resolve(ready);
  if (FAILED.has(spec.key)) return Promise.resolve(null);

  const inflight = INFLIGHT.get(spec.key);
  if (inflight) return inflight;

  const promise = buildVenv(spec, onProgress)
    .catch((err) => {
      FAILED.add(spec.key);
      console.warn(
        '[sandbox] venv build failed for',
        spec.key,
        err instanceof Error ? err.message : err
      );
      return null;
    })
    .finally(() => {
      INFLIGHT.delete(spec.key);
    });

  INFLIGHT.set(spec.key, promise);
  return promise;
}

async function buildVenv(spec: VenvSpec, onProgress?: ProgressFn): Promise<string | null> {
  const dir = venvDir(spec.key);
  mkdirSync(venvRoot(), { recursive: true });

  const python = venvPython(dir);
  if (!existsSync(python)) {
    onProgress?.('creating python environment…');
    const created = await run('uv', ['venv', '--python', '3.11', dir], INSTALL_TIMEOUT_MS);
    if (created.exitCode !== 0) {
      throw new Error(created.stderr.trim().split('\n').pop() || 'uv venv failed');
    }
  }

  const indexArgs: string[] = [];
  if (requirementsUsesTorchIndex(spec.requirementsPath)) {
    indexArgs.push(
      '--index-url', await resolveTorchIndex(),
      '--extra-index-url', PYPI_EXTRA_INDEX,
      '--index-strategy', 'unsafe-best-match'
    );
  }

  onProgress?.('installing dependencies (once per requirement set)…');
  const installed = await run(
    'uv',
    ['pip', 'install', '--python', python, ...indexArgs, '-r', spec.requirementsPath!],
    INSTALL_TIMEOUT_MS
  );
  if (installed.exitCode !== 0) {
    throw new Error(installed.stderr.trim().split('\n').pop() || 'uv pip install failed');
  }

  writeFileSync(path.join(dir, READY_MARKER), spec.key, 'utf-8');
  onProgress?.('environment ready.');
  return python;
}

interface RunResult {
  exitCode: number | null;
  stdout: string;
  stderr: string;
}

function run(cmd: string, args: string[], timeoutMs: number): Promise<RunResult> {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    let settled = false;

    const proc = spawn(cmd, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
      env: childEnv()
    });

    const finish = (result: RunResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    const timer = setTimeout(() => {
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      finish({ exitCode: null, stdout, stderr: `${stderr}\n${cmd} timed out` });
    }, timeoutMs);

    proc.stdout?.on('data', (b: Buffer) => { stdout += b.toString(); });
    proc.stderr?.on('data', (b: Buffer) => { stderr += b.toString(); });
    proc.on('error', (err) => finish({ exitCode: null, stdout, stderr: err.message }));
    proc.on('close', (code) => finish({ exitCode: code, stdout, stderr }));
  });
}

/** Convenience: spec straight from a module's requirements path. */
export function venvSpecFor(requirementsPath: string | undefined): VenvSpec {
  return {
    key: requirementsKey(requirementsPath),
    ...(requirementsPath ? { requirementsPath } : {})
  };
}
