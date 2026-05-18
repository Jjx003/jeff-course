/**
 * GET /api/sandbox/capabilities
 *
 * Returns the cached SandboxCapabilities snapshot. Use ?refresh=1 to
 * force a re-probe (e.g. after the user installs Docker Desktop).
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getCapabilities, refreshCapabilities } from '$lib/server/sandbox/runtime/detect.js';

export const GET: RequestHandler = async ({ url }) => {
  const refresh = url.searchParams.get('refresh');
  const caps = refresh === '1' || refresh === 'true'
    ? await refreshCapabilities()
    : await getCapabilities();
  return json(caps);
};
