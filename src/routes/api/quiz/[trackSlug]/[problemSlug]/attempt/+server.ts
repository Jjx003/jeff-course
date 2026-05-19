/**
 * POST /api/quiz/[trackSlug]/[problemSlug]/attempt
 *
 * Body: { total, correct, durationMs }
 *
 * Records the attempt and, on the first passing attempt for the module,
 * upserts the `reading_completions` row (which is how a quiz becomes
 * "completed" + grants its 5 points + counts toward streaks).
 *
 * Response: { passed, bestScore, bestTotal, attempts, wasNewCompletion }
 */

import { json } from '@sveltejs/kit';
import { randomUUID } from 'node:crypto';
import type { RequestHandler } from './$types';
import { recordQuizAttempt } from '$lib/server/stats.js';

interface AttemptBody {
  total: number;
  correct: number;
  durationMs?: number;
}

function isAttemptBody(value: unknown): value is AttemptBody {
  if (!value || typeof value !== 'object') return false;
  const o = value as Record<string, unknown>;
  return typeof o.total === 'number' && typeof o.correct === 'number';
}

export const POST: RequestHandler = async ({ params, request }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'invalid JSON body' }, { status: 400 });
  }
  if (!isAttemptBody(body)) {
    return json({ error: 'missing total/correct' }, { status: 400 });
  }

  const result = await recordQuizAttempt({
    id: randomUUID(),
    problemId,
    total: body.total,
    correct: body.correct,
    durationMs: typeof body.durationMs === 'number' ? body.durationMs : 0
  });

  return json(result);
};
