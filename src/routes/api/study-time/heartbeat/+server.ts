/**
 * POST /api/study-time/heartbeat
 *
 * Body: { sessionId, problemId, activeMs, startedAt }
 *
 * Upserts the running active-ms counter for one study session. Heartbeats
 * are fire-and-forget on the client side, so the server stays defensive:
 * malformed bodies or insane payloads return 400 rather than throwing.
 */

import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { upsertHeartbeat, MAX_SESSION_MS } from '$lib/server/studyTime.js';

interface HeartbeatBody {
  sessionId?: unknown;
  problemId?: unknown;
  activeMs?: unknown;
  startedAt?: unknown;
}

function bad(message: string): never {
  // `error()` throws under the hood; wrapping it makes the control flow
  // obvious to TypeScript so subsequent code can rely on narrowed types.
  throw error(400, message);
}

export const POST: RequestHandler = async ({ request }) => {
  let body: HeartbeatBody;
  try {
    body = (await request.json()) as HeartbeatBody;
  } catch {
    bad('Invalid JSON');
  }

  const sessionId = typeof body.sessionId === 'string' ? body.sessionId : null;
  const problemId = typeof body.problemId === 'string' ? body.problemId : null;
  const activeMs = typeof body.activeMs === 'number' ? body.activeMs : null;
  const startedAt = typeof body.startedAt === 'number' ? body.startedAt : null;

  if (sessionId === null) bad('Invalid sessionId');
  if (problemId === null) bad('Invalid problemId');
  if (activeMs === null) bad('Invalid activeMs');
  if (startedAt === null) bad('Invalid startedAt');

  if (sessionId.length === 0 || sessionId.length > 128) bad('Invalid sessionId');
  if (problemId.length === 0 || problemId.length > 256 || !problemId.includes('/')) {
    bad('Invalid problemId');
  }
  if (!Number.isFinite(activeMs) || activeMs < 0 || activeMs > MAX_SESSION_MS) {
    bad('Invalid activeMs');
  }
  if (!Number.isFinite(startedAt) || startedAt <= 0) bad('Invalid startedAt');

  await upsertHeartbeat(sessionId, problemId, activeMs, startedAt);
  return json({ ok: true });
};
