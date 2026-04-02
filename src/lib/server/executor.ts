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
import { writeFileSync, unlinkSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

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

  if (actual === expected) {
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
    let cmd: string;
    let args: string[];

    if (requirementsPath) {
      // uv run with specific requirements file — UV caches envs by requirements hash
      cmd = 'uv';
      args = ['run', '--python', '3.11', '-r', requirementsPath, 'python3', tmpFile];
    } else {
      cmd = 'uv';
      args = ['run', 'python3', tmpFile];
    }

    return await spawnAsync(cmd, args, {}, timeoutMs);
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
    const compileResult = await spawnAsync('g++', ['-O2', '-o', tmpBin, tmpSrc], {}, 30_000);
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
