/**
 * POST /api/sessions/[id]/cancel
 *
 * Graceful cancel — for baremetal this is equivalent to a tree-kill; for
 * docker the runtime will issue `docker stop --time=2` and only fall back
 * to `docker kill -s KILL` if the container ignores the signal.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { cancelSession } from '$lib/server/sandbox/index.js';

export const POST: RequestHandler = async ({ params }) => {
  await cancelSession(params.id);
  return json({ ok: true });
};
