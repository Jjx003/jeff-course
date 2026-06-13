/**
 * GET /api/stats
 *
 * Returns the aggregated gamification payload (streak, points, achievements,
 * activity heatmap, per-track progress). Server is the single source of truth;
 * the client never tries to compute these locally.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getStatsSummary } from '$lib/server/stats.js';

export const GET: RequestHandler = async ({ locals }) => {
  const stats = await getStatsSummary(locals.user!.id);
  return json({ stats });
};
