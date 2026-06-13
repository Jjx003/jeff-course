/**
 * GET  /api/reading/[trackSlug]/[problemSlug] — completion status
 * POST /api/reading/[trackSlug]/[problemSlug] — mark complete (idempotent)
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { isReadingCompleted, markReadingCompleted } from '$lib/server/stats.js';

export const GET: RequestHandler = async ({ locals, params }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const completed = await isReadingCompleted(locals.user!.id, problemId);
  return json({ completed });
};

export const POST: RequestHandler = async ({ locals, params }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const { wasNew } = await markReadingCompleted(locals.user!.id, problemId);
  return json({ wasNew });
};
