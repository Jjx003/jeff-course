import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { isEnrolled } from '$lib/server/enrollments';
import { getDeckProgress } from '$lib/server/flashcards';

export const GET: RequestHandler = async ({ locals, params }) => {
  if (!(await isEnrolled(locals.user!.id, params.trackSlug))) {
    error(403, 'not enrolled in this track');
  }
  const problem = await localCourseRepository.getProblem(params.trackSlug, params.problemSlug);
  if (!problem || problem.type !== 'flashcards') {
    error(404, 'flashcard deck not found');
  }
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const cardIds = (problem.deck?.cards ?? []).map((card) => card.id);
  return json(await getDeckProgress(locals.user!.id, problemId, cardIds));
};
