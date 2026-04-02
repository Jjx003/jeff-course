/**
 * GET /api/runs/[trackSlug]/[problemSlug]
 *
 * Returns all stored runs for a problem (one per language, newest first).
 * Used on page load to restore the OutputPanel state.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { dbReady, dbAll } from '$lib/server/db.js';
import type { RunSnapshot } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

type RunRow = { id: string; language: string; code: string; result: string; timestamp: number };

export const GET: RequestHandler = async ({ params }) => {
  await dbReady;
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const rows = await dbAll<RunRow>(
    'SELECT id, language, code, result, timestamp FROM runs WHERE problem_id = ? ORDER BY timestamp DESC',
    [problemId]
  );
  const runs: RunSnapshot[] = rows.map((row) => ({
    id: row.id,
    problemId,
    language: row.language as Language,
    code: row.code,
    result: JSON.parse(row.result),
    timestamp: Number(row.timestamp)
  }));
  return json({ runs });
};
