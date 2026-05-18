/**
 * GET  /api/sandbox/preferences/[trackSlug]   — return preferred mode + resources
 * PUT  /api/sandbox/preferences/[trackSlug]   — persist a new preference
 *
 * Used by the problem page's run-mode picker to remember the user's
 * sandbox choice per track.
 */

import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getPreference, upsertPreference } from '$lib/server/sandbox/persistence.js';
import type { ResourceLimits, SandboxMode, TrackPreference } from '$lib/server/sandbox/types.js';
import { defaultResourcesFor } from '$lib/server/sandbox/types.js';

const VALID_MODES: readonly SandboxMode[] = ['baremetal', 'docker', 'docker-gpu'];

export const GET: RequestHandler = async ({ params }) => {
  const pref = await getPreference(params.trackSlug);
  if (!pref) {
    // Return a default rather than 404 so the UI doesn't special-case the
    // first-visit shape. The default mode is baremetal — safe everywhere.
    const defaults: TrackPreference = {
      trackSlug: params.trackSlug,
      preferredMode: 'baremetal',
      resources: defaultResourcesFor('baremetal')
    };
    return json(defaults);
  }
  return json(pref);
};

interface PutBody {
  preferredMode?: SandboxMode;
  resources?: Partial<ResourceLimits>;
}

export const PUT: RequestHandler = async ({ params, request }) => {
  let body: PutBody;
  try {
    body = (await request.json()) as PutBody;
  } catch {
    throw error(400, 'Invalid JSON body');
  }
  const mode: SandboxMode = body.preferredMode && VALID_MODES.includes(body.preferredMode)
    ? body.preferredMode
    : 'baremetal';
  const defaults = defaultResourcesFor(mode);
  const resources: ResourceLimits = {
    memoryMb: body.resources?.memoryMb ?? defaults.memoryMb,
    cpus: body.resources?.cpus ?? defaults.cpus,
    gpu: body.resources?.gpu ?? defaults.gpu,
    timeoutMs: body.resources?.timeoutMs ?? defaults.timeoutMs
  };
  await upsertPreference({
    trackSlug: params.trackSlug,
    preferredMode: mode,
    resources
  });
  return json({ ok: true });
};
