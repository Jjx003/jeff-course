import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { isEnrolled } from '$lib/server/enrollments';
import { getDeckProgress, resetDeck } from '$lib/server/flashcards';

/**
 * Wipe scheduling state for one deck. The review log and the module's
 * completion record are left alone: the learner did do the work, and losing
 * the completion because they wanted a clean re-run would be a bad trade.
 */
export const POST: RequestHandler = async ({ locals, params }) => {
  if (!(await isEnrolled(locals.user!.id, params.trackSlug))) {
    error(403, 'not enrolled in this track');
  }
  const problem = await localCourseRepository.getProblem(params.trackSlug, params.problemSlug);
  if (!problem || problem.type !== 'flashcards') {
    error(404, 'flashcard deck not found');
  }
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  await resetDeck(locals.user!.id, problemId);
  const cardIds = (problem.deck?.cards ?? []).map((card) => card.id);
  return json(await getDeckProgress(locals.user!.id, problemId, cardIds));
};
