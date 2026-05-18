/**
 * POST /api/execute  —  legacy compat shim
 *
 * The original endpoint accepted { action, language, code, problemId } and
 * synchronously returned RunResult / SubmitResult. The new pipeline is the
 * session-oriented API in /api/sessions/* with live SSE output.
 *
 * For backwards compatibility (e.g. tooling or older client builds) this
 * shim accepts the same body, starts a baremetal session, awaits its
 * completion, and folds the result back into the legacy response shape.
 *
 * Cancellation: the caller's `request.signal` is wired through so closing
 * the connection cancels the underlying session.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { startSession, getSession, cancelSession, collectOutput } from '$lib/server/sandbox/index.js';
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
  if (!action || !language || code === undefined || !problemId) {
    throw error(400, 'Missing required fields: action, language, code, problemId');
  }
  if (action !== 'run' && action !== 'submit') {
    throw error(400, `Invalid action: ${action}`);
  }
  if (language !== 'python' && language !== 'cpp') {
    throw error(400, `Unsupported language: ${language}`);
  }

  const { id } = await startSession({
    problemId,
    language: language as Language,
    code,
    action,
    mode: 'baremetal'
  });

  // Cancel the underlying session if the HTTP request goes away.
  const onAbort = () => { void cancelSession(id); };
  request.signal.addEventListener('abort', onAbort, { once: true });

  const collected = await collectOutput(id);
  request.signal.removeEventListener('abort', onAbort);

  const finalRecord = await getSession(id);

  if (action === 'run') {
    const status: RunResult['status'] =
      collected.status === 'killed' ? 'timeout'
      : collected.status === 'cancelled' ? 'error'
      : collected.status === 'completed' ? 'ok'
      : 'error';
    const runResult: RunResult = {
      stdout: collected.stdout,
      stderr: collected.status === 'cancelled' ? 'Cancelled' : collected.stderr,
      durationMs: collected.durationMs,
      success: collected.status === 'completed',
      status
    };
    return json(runResult);
  }

  // action === 'submit'
  const verdict = (finalRecord?.submitVerdict ?? 'error') as SubmitResult['verdict'];
  const message = finalRecord?.submitMessage ?? collected.stderr ?? 'Submission failed.';
  const score = finalRecord?.submitScore ?? (verdict === 'accepted' ? 100 : 0);
  const submitResult: SubmitResult = {
    verdict,
    message,
    score: verdict === 'pending' ? null : score,
    testResults: verdict === 'pending' ? undefined : [
      {
        name: 'Expected output comparison',
        passed: verdict === 'accepted',
        actual: collected.stdout,
        durationMs: collected.durationMs
      }
    ]
  };
  return json(submitResult);
};
