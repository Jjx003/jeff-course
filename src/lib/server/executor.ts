/**
 * executor.ts
 *
 * Server-side code execution using Node.js child_process.spawn.
 *
 * - Python: executed via `uv run` (with optional requirements.txt for deps)
 * - C++: compiled with g++ then run as a subprocess
 *
 * Uses spawn (not exec/execSync) to avoid shell injection and to support
 * streaming stdout/stderr and reliable timeout via SIGKILL.
 *
 * SERVER-SIDE ONLY — never import this from client-side code or components.
 */

import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { writeFileSync, unlinkSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

// ── CUDA detection ────────────────────────────────────────────────────────
//
// Probe for an NVIDIA GPU once at module load time so we don't re-run
// nvidia-smi on every execution request.  The result is used to pick
// the right PyTorch wheel index when a requirements.txt includes torch.
//
// Index strategy:
//   CUDA present  → primary index = pytorch.org/whl/cu124
//                   extra index   = pypi.org/simple  (for non-torch deps)
//   CPU only      → primary index = pytorch.org/whl/cpu
//                   extra index   = pypi.org/simple
//
// Using pytorch.org as the PRIMARY index ensures the CUDA (or CPU) variant
// wins over the CPU-only wheel on pypi.org (which uv would otherwise prefer
// because it has no local-version suffix like +cu124).

const PYTORCH_CPU_INDEX  = 'https://download.pytorch.org/whl/cpu';
const PYTORCH_CUDA_INDEX = 'https://download.pytorch.org/whl/cu124';
const PYPI_EXTRA_INDEX   = 'https://pypi.org/simple';

// Allow explicit override via env var (e.g. for a different CUDA version).
const TORCH_INDEX_URL: string | null = process.env.TORCH_INDEX_URL ?? null;

async function detectCudaIndex(): Promise<string> {
  if (TORCH_INDEX_URL) return TORCH_INDEX_URL;
  return new Promise((resolve) => {
    const proc = spawn('nvidia-smi', ['--query-gpu=name', '--format=csv,noheader'], {
      stdio: ['ignore', 'pipe', 'ignore']
    });
    proc.on('close', (code) => resolve(code === 0 ? PYTORCH_CUDA_INDEX : PYTORCH_CPU_INDEX));
    proc.on('error', () => resolve(PYTORCH_CPU_INDEX));
  });
}

// Resolved once; all runPython calls await this.
const torchIndexPromise: Promise<string> = detectCudaIndex();

/** Return true if a requirements file lists torch as a dependency. */
function requirementsUsesTorchIndex(reqPath: string): boolean {
  try {
    const content = readFileSync(reqPath, 'utf-8');
    return /^\s*torch[>=<!,\s]/m.test(content);
  } catch {
    return false;
  }
}

// ── Types ─────────────────────────────────────────────────────────────────

export interface SpawnResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
}

export interface SubmitResult {
  passed: boolean;
  stdout: string;
  stderr: string;
  diff?: string;
  durationMs: number;
}

// ── Core spawn wrapper ────────────────────────────────────────────────────

/**
 * Spawn a process, collect stdout/stderr, and resolve when it closes.
 * Kills the process with SIGKILL if it exceeds timeoutMs.
 *
 * Uses event-based spawn (not execSync/exec) to:
 * - Avoid blocking the Node.js event loop
 * - Support reliable kill/timeout without shell buffering
 * - Stream output incrementally
 */
function spawnAsync(
  cmd: string,
  args: string[],
  opts: { cwd?: string; env?: NodeJS.ProcessEnv },
  timeoutMs: number
): Promise<SpawnResult> {
  return new Promise((resolve) => {
    const proc = spawn(cmd, args, { ...opts, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const start = Date.now();

    proc.stdout.on('data', (chunk: Buffer) => {
      stdout += chunk.toString();
    });
    proc.stderr.on('data', (chunk: Buffer) => {
      stderr += chunk.toString();
    });

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill('SIGKILL');
    }, timeoutMs);

    proc.on('close', (exitCode) => {
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode, timedOut, durationMs: Date.now() - start });
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      resolve({
        stdout,
        stderr: err.message,
        exitCode: null,
        timedOut: false,
        durationMs: Date.now() - start
      });
    });
  });
}

// ── Public API ────────────────────────────────────────────────────────────

/**
 * Run code in the given language and return stdout/stderr/timing.
 *
 * @param language      'python' | 'cpp'
 * @param code          Source code string
 * @param requirementsPath  Absolute path to requirements.txt (Python only, optional)
 * @param timeoutMs     Max wall-clock time before SIGKILL (default 10s)
 */
export async function runCode(
  language: 'python' | 'cpp',
  code: string,
  requirementsPath?: string,
  timeoutMs = 10_000
): Promise<RunResult> {
  if (language === 'python') {
    return runPython(code, requirementsPath, timeoutMs);
  }
  if (language === 'cpp') {
    return runCpp(code, timeoutMs);
  }
  return {
    stdout: '',
    stderr: `Unsupported language: ${language}`,
    exitCode: 1,
    timedOut: false,
    durationMs: 0
  };
}

/**
 * Run code and compare its stdout against expectedOutput.
 * Returns a SubmitResult including a diff string if output doesn't match.
 */
export async function submitCode(
  language: 'python' | 'cpp',
  code: string,
  expectedOutput: string,
  requirementsPath?: string,
  timeoutMs = 10_000
): Promise<SubmitResult> {
  const result = await runCode(language, code, requirementsPath, timeoutMs);

  if (result.timedOut) {
    return {
      passed: false,
      stdout: result.stdout,
      stderr: 'Execution timed out',
      durationMs: result.durationMs
    };
  }

  if (result.exitCode !== 0) {
    return {
      passed: false,
      stdout: result.stdout,
      stderr: result.stderr || `Process exited with code ${result.exitCode}`,
      durationMs: result.durationMs
    };
  }

  const actual = normalizeOutput(result.stdout);
  const expected = normalizeOutput(expectedOutput);

  if (actual === expected || fuzzyMatch(expected, actual)) {
    return {
      passed: true,
      stdout: result.stdout,
      stderr: result.stderr,
      durationMs: result.durationMs
    };
  }

  return {
    passed: false,
    stdout: result.stdout,
    stderr: result.stderr,
    diff: buildDiff(expected, actual),
    durationMs: result.durationMs
  };
}

// ── Language runners ──────────────────────────────────────────────────────

async function runPython(
  code: string,
  requirementsPath: string | undefined,
  timeoutMs: number
): Promise<RunResult> {
  const tmpFile = path.join(tmpdir(), `${randomUUID()}.py`);
  writeFileSync(tmpFile, code, 'utf-8');

  try {
    let args: string[];

    if (requirementsPath) {
      if (requirementsUsesTorchIndex(requirementsPath)) {
        // Route torch through the right wheel server (CUDA or CPU) so uv
        // installs the GPU-enabled build when an NVIDIA GPU is present.
        // --index-strategy unsafe-best-match is required because torch exists
        // on both pypi.org (cpu-only) and the pytorch wheel server (+cu124);
        // without it uv stops at the first index that has the package (PyPI)
        // and never sees the CUDA build.
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

    return await spawnAsync('uv', args, {}, timeoutMs);
  } finally {
    tryUnlink(tmpFile);
  }
}

async function runCpp(code: string, timeoutMs: number): Promise<RunResult> {
  const id = randomUUID();
  const tmpSrc = path.join(tmpdir(), `${id}.cpp`);
  const tmpBin = path.join(tmpdir(), id);
  writeFileSync(tmpSrc, code, 'utf-8');

  try {
    // Compile step
    const compileResult = await spawnAsync('g++', ['-std=c++17', '-O2', '-o', tmpBin, tmpSrc], {}, 30_000);
    if (compileResult.exitCode !== 0) {
      return {
        stdout: '',
        stderr: compileResult.stderr || 'Compilation failed',
        exitCode: compileResult.exitCode,
        timedOut: false,
        durationMs: compileResult.durationMs
      };
    }

    // Run step
    const runResult = await spawnAsync(tmpBin, [], {}, timeoutMs);
    return {
      ...runResult,
      // Add compile time to total duration
      durationMs: compileResult.durationMs + runResult.durationMs
    };
  } finally {
    tryUnlink(tmpSrc);
    tryUnlink(tmpBin);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────

/** Trim trailing whitespace per line, then trim the whole string. */
function normalizeOutput(s: string): string {
  return s
    .split('\n')
    .map((line) => line.trimEnd())
    .join('\n')
    .trim();
}

// Matches integers and floating-point numbers (with optional exponent).
const NUM_RE = /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g;

/**
 * Compare two output strings with fuzzy numeric tolerance.
 *
 * Rules:
 *  - Non-numeric tokens must match exactly (same text, same position).
 *  - Numeric tokens are compared as floats; they pass if
 *    |actual - expected| <= epsilon  OR  |actual - expected| / |expected| <= epsilon
 *    (absolute OR relative tolerance — mirrors numpy.allclose behaviour).
 *  - Line count must be identical.
 */
function fuzzyMatch(expected: string, actual: string, epsilon = 1e-3): boolean {
  const expLines = expected.split('\n');
  const actLines = actual.split('\n');
  if (expLines.length !== actLines.length) return false;

  for (let i = 0; i < expLines.length; i++) {
    const eLine = expLines[i];
    const aLine = actLines[i];
    if (eLine === aLine) continue;

    // Tokenise both lines into alternating [text, number, text, number, ...] chunks.
    const eTokens = tokenizeLine(eLine);
    const aTokens = tokenizeLine(aLine);
    if (eTokens.length !== aTokens.length) return false;

    for (let j = 0; j < eTokens.length; j++) {
      const et = eTokens[j];
      const at = aTokens[j];
      if (et.isNum && at.isNum) {
        const ev = et.num!;
        const av = at.num!;
        const absDiff = Math.abs(av - ev);
        const relDiff = Math.abs(ev) > 1e-10 ? absDiff / Math.abs(ev) : absDiff;
        if (absDiff > epsilon && relDiff > epsilon) return false;
      } else {
        if (et.text !== at.text) return false;
      }
    }
  }
  return true;
}

interface Token { isNum: boolean; text: string; num?: number }

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  let last = 0;
  for (const m of line.matchAll(new RegExp(NUM_RE.source, 'g'))) {
    const start = m.index!;
    if (start > last) tokens.push({ isNum: false, text: line.slice(last, start) });
    tokens.push({ isNum: true, text: m[0], num: parseFloat(m[0]) });
    last = start + m[0].length;
  }
  if (last < line.length) tokens.push({ isNum: false, text: line.slice(last) });
  return tokens;
}

/**
 * Build a simple unified-style diff between expected and actual output.
 * Lines present in expected but not actual are prefixed with `-`,
 * lines present in actual but not expected are prefixed with `+`.
 */
function buildDiff(expected: string, actual: string): string {
  const expLines = expected.split('\n');
  const actLines = actual.split('\n');
  const maxLen = Math.max(expLines.length, actLines.length);
  const diffLines: string[] = ['--- expected', '+++ actual'];

  for (let i = 0; i < maxLen; i++) {
    const e = expLines[i];
    const a = actLines[i];
    if (e === undefined) {
      diffLines.push(`+ ${a}`);
    } else if (a === undefined) {
      diffLines.push(`- ${e}`);
    } else if (e === a) {
      diffLines.push(`  ${e}`);
    } else {
      diffLines.push(`- ${e}`);
      diffLines.push(`+ ${a}`);
    }
  }

  return diffLines.join('\n');
}

function tryUnlink(filePath: string): void {
  try {
    if (existsSync(filePath)) {
      unlinkSync(filePath);
    }
  } catch {
    // Ignore cleanup errors
  }
}
