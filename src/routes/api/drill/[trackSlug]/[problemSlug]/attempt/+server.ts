import { json } from '@sveltejs/kit';
import { randomUUID } from 'node:crypto';
import type { RequestHandler } from './$types';
import { recordDrillAttempt } from '$lib/server/stats.js';

interface AttemptBody {
  total: number;
  correct: number;
  avgMs: number;
  bestStreak: number;
  durationMs: number;
  targetAccuracy?: number;
}

function isAttemptBody(value: unknown): value is AttemptBody {
  if (!value || typeof value !== 'object') return false;
  const o = value as Record<string, unknown>;
  return typeof o.total === 'number'
    && typeof o.correct === 'number'
    && typeof o.avgMs === 'number'
    && typeof o.bestStreak === 'number'
    && typeof o.durationMs === 'number';
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
    return json({ error: 'missing drill attempt metrics' }, { status: 400 });
  }

  const result = await recordDrillAttempt({
    id: randomUUID(),
    problemId,
    total: body.total,
    correct: body.correct,
    avgMs: body.avgMs,
    bestStreak: body.bestStreak,
    durationMs: body.durationMs,
    targetAccuracy: typeof body.targetAccuracy === 'number' ? body.targetAccuracy : undefined
  });

  return json(result);
};
