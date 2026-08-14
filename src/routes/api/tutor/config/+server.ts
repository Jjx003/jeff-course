/**
 * GET /api/tutor/config — whether the AI tutor is usable on this server.
 *
 * Only the enabled flag and model name cross the wire; the OpenRouter key
 * never leaves the server process.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { readTutorSettings } from '$lib/server/tutor/config.js';
import type { TutorConfig } from '$lib/types/tutor.js';

export const GET: RequestHandler = async () => {
  const settings = readTutorSettings();
  const config: TutorConfig = settings.apiKey
    ? { enabled: true, model: settings.model }
    : {
        enabled: false,
        model: settings.model,
        reason: 'Set OPENROUTER_API_KEY in the server environment to enable the tutor.'
      };
  return json(config);
};
