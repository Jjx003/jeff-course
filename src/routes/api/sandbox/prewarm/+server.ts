/**
 * POST /api/sandbox/prewarm
 *
 * Body: { problemId: "track/module" }
 *
 * Asks the warm-process pool to have a host ready for this module's
 * requirement set. Called when a coding module opens, so the torch import
 * happens while the learner reads the problem statement instead of after
 * they press Run.
 *
 * Fire-and-forget by design: returns immediately, never blocks on the warm,
 * and a failure here only means the next run takes the slow path.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { prewarmForProblem } from '$lib/server/sandbox/index.js';

export const POST: RequestHandler = async ({ request }) => {
  let problemId: unknown;
  try {
    ({ problemId } = await request.json());
  } catch {
    return json({ warming: false, reason: 'invalid body' }, { status: 400 });
  }

  if (typeof problemId !== 'string' || !problemId.includes('/')) {
    return json({ warming: false, reason: 'invalid problemId' }, { status: 400 });
  }

  return json(prewarmForProblem(problemId));
};
