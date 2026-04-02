/**
 * POST /api/execute
 *
 * Executes user code for a given problem and language.
 *
 * Body:
 *   {
 *     action: 'run' | 'submit',
 *     language: 'python' | 'cpp',
 *     code: string,
 *     problemId: string,   // "{trackSlug}/{problemSlug}"
 *   }
 *
 * For 'run': spawns the code and returns stdout/stderr/timing.
 * For 'submit': compares stdout against expected_output/<lang>.txt.
 *   If no expected output is configured, returns verdict 'pending'.
 */

import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { runCode, submitCode } from '$lib/server/executor.js';
import { loadProblem } from '$lib/content/courseLoader.js';
import type { Language } from '$lib/types/course.js';
import type { RunResult, SubmitResult } from '$lib/types/execution.js';

interface ExecuteBody {
  action: 'run' | 'submit';
  language: string;
  code: string;
  problemId: string;
}

export const POST: RequestHandler = async ({ request }) => {
  let body: ExecuteBody;
  try {
    body = await request.json();
  } catch {
    throw error(400, 'Invalid JSON body');
  }

  const { action, language, code, problemId } = body;

  if (!action || !language || !code || !problemId) {
    throw error(400, 'Missing required fields: action, language, code, problemId');
  }
  if (action !== 'run' && action !== 'submit') {
    throw error(400, `Invalid action: ${action}. Must be 'run' or 'submit'`);
  }
  if (language !== 'python' && language !== 'cpp') {
    throw error(400, `Unsupported language: ${language}`);
  }

  const lang = language as Language;

  // Resolve problem to get requirementsPath and expectedOutput
  const [trackSlug, problemSlug] = problemId.split('/');
  if (!trackSlug || !problemSlug) {
    throw error(400, `Invalid problemId format: expected "trackSlug/problemSlug"`);
  }

  const problem = await loadProblem(trackSlug, problemSlug);
  if (!problem) {
    throw error(404, `Problem not found: ${problemId}`);
  }

  const requirementsPath = problem.requirementsPath;

  if (action === 'run') {
    const result = await runCode(lang, code, requirementsPath);

    const runResult: RunResult = {
      stdout: result.stdout,
      stderr: result.stderr,
      durationMs: result.durationMs,
      success: result.exitCode === 0 && !result.timedOut,
      status: result.timedOut ? 'timeout' : result.exitCode === 0 ? 'ok' : 'error'
    };

    return json(runResult);
  }

  // action === 'submit'
  const expectedOutput = problem.expectedOutput?.[lang];

  if (!expectedOutput) {
    const submitResult: SubmitResult = {
      verdict: 'pending',
      message: 'No expected output configured for this language.',
      score: null
    };
    return json(submitResult);
  }

  const result = await submitCode(lang, code, expectedOutput, requirementsPath);

  const submitResult: SubmitResult = {
    verdict: result.passed ? 'accepted' : result.stderr ? 'error' : 'wrong_answer',
    message: result.passed
      ? 'All outputs matched.'
      : result.stderr
        ? result.stderr
        : 'Output did not match expected.',
    score: result.passed ? 100 : 0,
    testResults: [
      {
        name: 'Expected output comparison',
        passed: result.passed,
        expected: expectedOutput,
        actual: result.stdout,
        durationMs: result.durationMs
      }
    ]
  };

  return json(submitResult);
};
