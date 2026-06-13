/**
 * GET  /api/submissions/[trackSlug]/[problemSlug]  — accepted submissions only (for the picker), newest first
 * POST /api/submissions/[trackSlug]/[problemSlug]  — persist all submissions
 */

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { dbReady, dbRun, dbAll } from '$lib/server/db.js';
import type { SubmitSnapshot } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

type SubmitRow = { id: string; language: string; code: string; result: string; timestamp: number };

export const GET: RequestHandler = async ({ locals, params }) => {
  await dbReady;
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const rows = await dbAll<SubmitRow>(
    'SELECT id, language, code, result, timestamp FROM submissions WHERE user_id = ? AND problem_id = ? ORDER BY timestamp DESC',
    [locals.user!.id, problemId]
  );
  const submissions: SubmitSnapshot[] = rows
    .map((row) => ({
      id: row.id,
      problemId,
      language: row.language as Language,
      code: row.code,
      result: JSON.parse(row.result) as SubmitSnapshot['result'],
      timestamp: Number(row.timestamp)
    }))
    .filter((s) => s.result.verdict === 'accepted');
  return json({ submissions });
};

export const POST: RequestHandler = async ({ locals, params, request }) => {
  await dbReady;
  const snapshot = (await request.json()) as SubmitSnapshot;

  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  await dbRun(
    'INSERT INTO submissions (id, user_id, problem_id, language, code, result, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [
      snapshot.id,
      locals.user!.id,
      problemId,
      snapshot.language,
      snapshot.code,
      JSON.stringify(snapshot.result),
      snapshot.timestamp
    ]
  );
  return json({ ok: true, saved: true });
};
