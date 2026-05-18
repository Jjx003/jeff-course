/**
 * POST /api/sessions/[id]/kill
 *
 * Force kill — SIGKILL / `docker kill -s KILL`. No graceful window.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { killSession } from '$lib/server/sandbox/index.js';

export const POST: RequestHandler = async ({ params }) => {
  await killSession(params.id);
  return json({ ok: true });
};
