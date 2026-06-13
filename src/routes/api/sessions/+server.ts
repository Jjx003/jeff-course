/**
 * Sessions API
 *
 *   POST /api/sessions     — start a new session
 *   GET  /api/sessions     — list sessions (?activeOnly=1, ?limit=N)
 *
 * The persistent session row gives the UI a stable handle to subscribe to
 * via /api/sessions/[id]/stream (SSE) and to cancel via the action routes.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { listSessions, startSession } from '$lib/server/sandbox/index.js';
import type {
  ResourceLimits,
  SandboxMode,
  StartSessionRequest
} from '$lib/server/sandbox/types.js';

const VALID_MODES: readonly SandboxMode[] = ['baremetal', 'docker', 'docker-gpu'];

export const POST: RequestHandler = async ({ locals, request }) => {
  let body: Partial<StartSessionRequest>;
  try {
    body = (await request.json()) as Partial<StartSessionRequest>;
  } catch {
    throw error(400, 'Invalid JSON body');
  }

  const { problemId, language, code, action } = body;
  if (!problemId || !language || typeof code !== 'string' || !action) {
    throw error(400, 'Missing required fields: problemId, language, code, action');
  }
  if (action !== 'run' && action !== 'submit') {
    throw error(400, `Invalid action: ${action}`);
  }
  if (language !== 'python' && language !== 'cpp') {
    throw error(400, `Unsupported language: ${language}`);
  }

  const mode: SandboxMode = body.mode && VALID_MODES.includes(body.mode) ? body.mode : 'baremetal';
  const resources: Partial<ResourceLimits> | undefined = body.resources ?? undefined;

  const result = await startSession({
    userId: locals.user!.id,
    problemId,
    language,
    code,
    action,
    mode,
    resources
  });

  return json({ id: result.id, queued: result.queued });
};

export const GET: RequestHandler = async ({ locals, url }) => {
  const activeOnly = url.searchParams.get('activeOnly');
  const limitRaw = url.searchParams.get('limit');
  const limit = limitRaw ? Math.max(1, Math.min(500, parseInt(limitRaw, 10))) : 100;

  const sessions = await listSessions(locals.user!.id, {
    activeOnly: activeOnly === '1' || activeOnly === 'true',
    limit
  });
  return json(sessions);
};
