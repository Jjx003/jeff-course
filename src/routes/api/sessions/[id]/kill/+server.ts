/**
 * POST /api/sessions/[id]/kill
 *
 * Force kill — SIGKILL / `docker kill -s KILL`. No graceful window.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getSession, killSession } from '$lib/server/sandbox/index.js';

export const POST: RequestHandler = async ({ locals, params }) => {
  const rec = await getSession(locals.user!.id, params.id);
  if (!rec) throw error(404, 'Session not found');
  await killSession(params.id);
  return json({ ok: true });
};
