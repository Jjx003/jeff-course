/**
 * /sessions page — server load.
 *
 * Returns the most recent 100 sessions (active + terminal) for the initial
 * render. The client polls /api/sessions every 2s to keep the table fresh.
 */

import type { PageServerLoad } from './$types';
import { listSessions } from '$lib/server/sandbox/index.js';

export const load: PageServerLoad = async () => ({
  initial: await listSessions({ limit: 100 })
});
