import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getDrillProgress } from '$lib/server/stats.js';

export const GET: RequestHandler = async ({ params, url }) => {
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const rawTarget = Number(url.searchParams.get('targetAccuracy'));
  const targetAccuracy = Number.isFinite(rawTarget) && rawTarget > 0 && rawTarget <= 1
    ? rawTarget
    : undefined;
  const progress = await getDrillProgress(problemId, targetAccuracy);
  return json(progress);
};
