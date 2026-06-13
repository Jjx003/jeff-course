import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { dbReady, dbRun, dbAll } from '$lib/server/db.js';
import type { Draft } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

type DraftRow = { code: string; last_saved_at: number };

export const GET: RequestHandler = async ({ locals, params }) => {
  await dbReady;
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const rows = await dbAll<DraftRow>(
    'SELECT code, last_saved_at FROM drafts WHERE user_id = ? AND problem_id = ? AND language = ?',
    [locals.user!.id, problemId, params.language]
  );
  if (!rows.length) return json({ draft: null });
  const draft: Draft = {
    problemId,
    language: params.language as Language,
    code: rows[0].code,
    lastSavedAt: Number(rows[0].last_saved_at)
  };
  return json({ draft });
};

export const PUT: RequestHandler = async ({ locals, params, request }) => {
  await dbReady;
  const { code } = (await request.json()) as { code: string };
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  await dbRun(
    `INSERT INTO drafts (user_id, problem_id, language, code, last_saved_at) VALUES (?, ?, ?, ?, ?)
     ON CONFLICT (user_id, problem_id, language)
     DO UPDATE SET code = EXCLUDED.code, last_saved_at = EXCLUDED.last_saved_at`,
    [locals.user!.id, problemId, params.language, code, Date.now()]
  );
  return json({ ok: true });
};
