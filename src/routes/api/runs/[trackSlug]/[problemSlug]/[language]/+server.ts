/**
 * PUT /api/runs/[trackSlug]/[problemSlug]/[language]
 *
 * Upserts the latest run for a (problem, language) pair.
 * Only one run row is kept per pair — each new Run click overwrites the previous.
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { dbReady, dbRun } from '$lib/server/db.js';
import type { RunSnapshot } from '$lib/types/execution.js';

export const PUT: RequestHandler = async ({ params, request }) => {
  await dbReady;
  const snapshot = (await request.json()) as RunSnapshot;
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  await dbRun(
    `INSERT INTO runs (problem_id, language, id, code, result, timestamp) VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT (problem_id, language)
     DO UPDATE SET id = EXCLUDED.id, code = EXCLUDED.code, result = EXCLUDED.result, timestamp = EXCLUDED.timestamp`,
    [
      problemId,
      params.language,
      snapshot.id,
      snapshot.code,
      JSON.stringify(snapshot.result),
      snapshot.timestamp
    ]
  );
  return json({ ok: true });
};
