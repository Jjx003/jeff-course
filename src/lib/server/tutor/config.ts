/**
 * AI tutor configuration, read from the environment.
 *
 * SERVER-SIDE ONLY. The API key must never reach the browser — the client
 * only ever learns whether the tutor is enabled and which model is in use.
 *
 * Unlike the rest of the server code, which reads `process.env` directly,
 * this uses `$env/dynamic/private`. That is what makes a repo-root `.env`
 * file work: SvelteKit loads `.env` into the `$env` modules only, never into
 * `process.env`. Both sources are visible through `$env/dynamic/private`, so
 * an exported shell variable and a `.env` entry behave the same way.
 */

import { env } from '$env/dynamic/private';

export const DEFAULT_TUTOR_MODEL = 'openai/gpt-4o-mini';
export const DEFAULT_OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1';

export interface TutorSettings {
  apiKey: string;
  model: string;
  baseUrl: string;
  /** When true the tutor may quote solution files and quiz answer keys. */
  allowSolutions: boolean;
}

function read(name: string): string {
  return env[name]?.trim() ?? '';
}

/** Read on every call so edits to `.env` take effect without a restart. */
export function readTutorSettings(): TutorSettings {
  return {
    apiKey: read('OPENROUTER_API_KEY'),
    model: read('OPENROUTER_MODEL') || DEFAULT_TUTOR_MODEL,
    baseUrl: read('OPENROUTER_BASE_URL') || DEFAULT_OPENROUTER_BASE_URL,
    allowSolutions: read('TUTOR_ALLOW_SOLUTIONS') === '1'
  };
}

export function isTutorEnabled(): boolean {
  return readTutorSettings().apiKey.length > 0;
}
