/**
 * GET    /api/tutor/[trackSlug]/[problemSlug] — this learner's saved thread
 * DELETE /api/tutor/[trackSlug]/[problemSlug] — clear the thread
 *
 * Streaming a new reply happens in `./message/+server.ts`.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { clearConversation, getConversation } from '$lib/server/tutor/conversations.js';

export const GET: RequestHandler = async ({ locals, params }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  return json(await getConversation(locals.user!.id, problemId));
};

export const DELETE: RequestHandler = async ({ locals, params }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  await clearConversation(locals.user!.id, problemId);
  return json({ ok: true });
};
