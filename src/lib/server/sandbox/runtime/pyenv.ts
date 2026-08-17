/**
 * Shared Python environment plumbing for the baremetal runtime and the warm
 * process pool.
 *
 * Both paths must build *identical* environments — a warm host that resolved
 * a different interpreter or a different torch index than the direct
 * `uv run` path would silently change what the learner's code sees. So the
 * uv argument construction, the torch index probe, and the extra env vars
 * all live here and are used by both.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

// ── Torch index resolution ────────────────────────────────────────────────
//
// PyPI's default `torch` wheel for Linux is the CUDA build (~2.5 GB). We
// pick an explicit index instead: cu124 when the host has an NVIDIA driver,
// CPU wheels otherwise. `TORCH_INDEX_URL` overrides the probe entirely.

export const PYTORCH_CPU_INDEX = 'https://download.pytorch.org/whl/cpu';
export const PYTORCH_CUDA_INDEX = 'https://download.pytorch.org/whl/cu124';
export const PYPI_EXTRA_INDEX = 'https://pypi.org/simple';

const TORCH_INDEX_URL = process.env.TORCH_INDEX_URL ?? null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;

/**
 * Probe `nvidia-smi` once per server process and cache the answer on
 * globalThis so Vite HMR doesn't re-run it.
 */
export function resolveTorchIndex(): Promise<string> {
  return (g.__sandboxTorchIdx ??= detectCudaIndex());
}

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

// ── requirements.txt inspection ───────────────────────────────────────────

/** Code point of the UTF-8 BOM, which PowerShell redirection likes to add. */
const BOM_CODE_POINT = 0xfeff;

/** BOM-tolerant read. Returns '' when the file is missing or unreadable. */
export function readRequirements(reqPath: string | undefined): string {
  if (!reqPath) return '';
  try {
    const raw = readFileSync(reqPath, 'utf-8');
    return raw.charCodeAt(0) === BOM_CODE_POINT ? raw.slice(1) : raw;
  } catch {
    return '';
  }
}

/** True when the requirement set pins `torch`, i.e. needs the torch index. */
export function requirementsUsesTorchIndex(reqPath: string | undefined): boolean {
  return /^\s*torch[>=<!,\s]/m.test(readRequirements(reqPath));
}

/**
 * Modules a warm host should import before it is handed out. Importing torch
 * costs 3–10s and CUDA init another second or two; doing it while the learner
 * is still reading the problem statement is the whole point of the pool.
 *
 * We only prewarm what the module actually declares — importing transformers
 * for a numpy-only exercise would waste ~700 MB of RSS for nothing.
 */
export function prewarmModulesFor(reqPath: string | undefined): string[] {
  const content = readRequirements(reqPath);
  if (!content.trim()) return [];
  const mods: string[] = [];
  if (/^\s*numpy[>=<!,\s]/m.test(content)) mods.push('numpy');
  if (/^\s*torch[>=<!,\s]/m.test(content)) mods.push('torch');
  if (/^\s*transformers[>=<!,\s]/m.test(content)) mods.push('transformers');
  return mods;
}

/**
 * Stable identity for a requirement set. Modules that declare byte-identical
 * requirements share one warm host, which matters because most of a course
 * repeats the same three lines.
 */
export function requirementsKey(reqPath: string | undefined): string {
  const content = readRequirements(reqPath).trim();
  if (!content) return 'plain';
  return createHash('sha256').update(content).digest('hex').slice(0, 16);
}

// ── uv invocation ─────────────────────────────────────────────────────────

export interface UvRunOpts {
  /** Absolute path to the script uv should execute. */
  script: string;
  /** Absolute path to requirements.txt, if the module declares one. */
  requirementsPath?: string;
  /**
   * Resolved torch index. Required when `requirementsPath` pins torch;
   * ignored otherwise. Callers get it from `resolveTorchIndex()`.
   */
  torchIndex?: string;
}

/**
 * Build the `uv run …` argv. This is the single definition of how a Python
 * run is launched on the host — the direct path and the pool both use it.
 */
export function uvRunArgs(opts: UvRunOpts): string[] {
  const { script, requirementsPath, torchIndex } = opts;
  if (!requirementsPath) {
    return ['run', 'python', script];
  }
  if (torchIndex) {
    return [
      'run', '--python', '3.11',
      '--index-url', torchIndex,
      '--extra-index-url', PYPI_EXTRA_INDEX,
      '--index-strategy', 'unsafe-best-match',
      '--with-requirements', requirementsPath,
      'python', script
    ];
  }
  return ['run', '--python', '3.11', '--with-requirements', requirementsPath, 'python', script];
}

// ── Child environment ─────────────────────────────────────────────────────

/**
 * Extra env applied to every sandboxed Python child, layered over
 * `process.env`. Operator-set values always win — each entry is only filled
 * in when it is absent from the parent environment.
 *
 *   PYTHONUNBUFFERED        stdout to a pipe is block-buffered by default,
 *                           which makes the live SSE tail arrive in 8 KB
 *                           lumps (or all at once at exit). Unbuffering is
 *                           what makes the output panel feel live.
 *   HF_HUB_ETAG_TIMEOUT     huggingface_hub revalidates every cached file
 *                           over HTTP on each `from_pretrained`. The default
 *                           10s-per-request stall on a flaky connection is
 *                           the difference between "slow" and "looks hung".
 *                           Downloads still work; only the wait is capped.
 *   HF_HUB_DISABLE_TELEMETRY  no phone-home from a local course app.
 *
 * Note: we deliberately do NOT force `HF_HUB_OFFLINE=1`. It would skip
 * revalidation entirely, but it also turns the first run of any module whose
 * weights aren't cached yet into a hard failure. Operators who have every
 * checkpoint cached can still set it themselves.
 */
export function sandboxEnv(): NodeJS.ProcessEnv {
  const out: NodeJS.ProcessEnv = {};
  const fill = (key: string, value: string) => {
    if (process.env[key] === undefined) out[key] = value;
  };
  fill('PYTHONUNBUFFERED', '1');
  fill('HF_HUB_ETAG_TIMEOUT', '3');
  fill('HF_HUB_DISABLE_TELEMETRY', '1');
  return out;
}

/** `process.env` with the sandbox additions layered on top. */
export function childEnv(extra?: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  return { ...process.env, ...sandboxEnv(), ...(extra ?? {}) };
}
