/**
 * GET /api/sessions/[id]
 *
 * Returns a single SessionRecord, or 404 if unknown.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getSession } from '$lib/server/sandbox/index.js';

export const GET: RequestHandler = async ({ params }) => {
  const rec = await getSession(params.id);
  if (!rec) throw error(404, 'Session not found');
  return json(rec);
};
