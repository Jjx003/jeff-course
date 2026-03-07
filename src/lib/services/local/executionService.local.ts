/**
 * LocalExecutionService
 *
 * Mock execution that runs entirely in the browser with no server round-trip.
 *
 * Behavior:
 * - Parses Python `print(...)` calls and echoes their arguments as stdout.
 * - Recognizes C++ `std::cout <<` and echoes those strings.
 * - Simulates a short delay to feel realistic.
 * - Always returns a successful result for the mock.
 *
 * EXTENSION POINT: Replace this with a RemoteExecutionService that POSTs
 * to a sandboxed backend. The interface contract (RunRequest → RunResult)
 * stays identical.
 *
 * CLIENT-SIDE ONLY (no Node.js APIs used).
 */

import type { ExecutionService } from '../executionService.js';
import type { RunRequest, RunResult, SubmitRequest, SubmitResult } from '$lib/types/execution.js';

// ── Mock helpers ──────────────────────────────────────────────────────────

function extractPythonOutput(code: string): string {
  const lines: string[] = [];
  const printRegex = /^\s*print\s*\(\s*(.*?)\s*\)\s*$/gm;
  let match: RegExpExecArray | null;
  while ((match = printRegex.exec(code)) !== null) {
    // Strip surrounding quotes for simple string literals
    let arg = match[1].trim();
    if ((arg.startsWith('"') && arg.endsWith('"')) ||
        (arg.startsWith("'") && arg.endsWith("'"))) {
      arg = arg.slice(1, -1);
    }
    // For f-strings or expressions, show the raw expression
    lines.push(arg);
  }
  return lines.join('\n');
}

function extractCppOutput(code: string): string {
  const lines: string[] = [];
  const coutRegex = /std::cout\s*<<\s*"([^"]+)"/g;
  let match: RegExpExecArray | null;
  while ((match = coutRegex.exec(code)) !== null) {
    lines.push(match[1]);
  }
  return lines.join('\n');
}

function simulatedOutput(language: string, code: string): string {
  if (language === 'python') {
    const extracted = extractPythonOutput(code);
    const header = '# [Local Mock] Python execution simulated\n';
    return extracted ? header + extracted : header + '(no output)';
  }
  if (language === 'cpp') {
    const extracted = extractCppOutput(code);
    const header = '// [Local Mock] C++ execution simulated\n';
    return extracted ? header + extracted : header + '(no output)';
  }
  return '[Local Mock] Execution simulated (no output)';
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

// ── Implementation ────────────────────────────────────────────────────────

export class LocalExecutionService implements ExecutionService {
  async run(request: RunRequest): Promise<RunResult> {
    // Simulate network + execution latency
    const delay = 300 + Math.random() * 400;
    await sleep(delay);

    const stdout = simulatedOutput(request.language, request.code);

    return {
      stdout,
      stderr: '',
      durationMs: Math.round(delay),
      success: true,
      status: 'ok'
    };
  }

  async submit(request: SubmitRequest): Promise<SubmitResult> {
    await sleep(600 + Math.random() * 600);

    // Local mock: always accept (replace with real test runner later).
    return {
      verdict: 'accepted',
      message:
        '[Local Mock] All test cases passed. ' +
        'Connect a real execution backend to run actual tests.',
      score: 100,
      testResults: [
        { name: 'Sample test 1', passed: true, durationMs: 12 },
        { name: 'Sample test 2', passed: true, durationMs: 8 }
      ]
    };
  }
}

export const localExecutionService = new LocalExecutionService();

// Utility: generate a unique run/submission ID
export { generateId };
