/**
 * POST /api/sessions/[id]/cancel
 *
 * Graceful cancel — for baremetal this is equivalent to a tree-kill; for
 * docker the runtime will issue `docker stop --time=2` and only fall back
 * to `docker kill -s KILL` if the container ignores the signal.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { cancelSession, getSession } from '$lib/server/sandbox/index.js';

export const POST: RequestHandler = async ({ locals, params }) => {
  const rec = await getSession(locals.user!.id, params.id);
  if (!rec) throw error(404, 'Session not found');
  await cancelSession(params.id);
  return json({ ok: true });
};
