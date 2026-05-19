/**
 * GET  /api/quiz/[trackSlug]/[problemSlug]          — aggregated quiz progress
 * POST /api/quiz/[trackSlug]/[problemSlug]/attempt  — record one attempt
 *
 * The POST path lives in `./attempt/+server.ts`; this file handles the GET.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getQuizProgress } from '$lib/server/stats.js';

export const GET: RequestHandler = async ({ params }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const progress = await getQuizProgress(problemId);
  return json(progress);
};
