import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { isEnrolled } from '$lib/server/enrollments';
import { isFlashcardGrade, recordFlashcardReview } from '$lib/server/flashcards';

export const POST: RequestHandler = async ({ locals, params, request }) => {
  if (!(await isEnrolled(locals.user!.id, params.trackSlug))) {
    error(403, 'not enrolled in this track');
  }
  const problem = await localCourseRepository.getProblem(params.trackSlug, params.problemSlug);
  if (!problem || problem.type !== 'flashcards') {
    error(404, 'flashcard deck not found');
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'invalid JSON body' }, { status: 400 });
  }

  const o = (body ?? {}) as Record<string, unknown>;
  if (typeof o.cardId !== 'string' || !isFlashcardGrade(o.grade)) {
    return json({ error: 'expected { cardId, grade, responseMs }' }, { status: 400 });
  }

  const cards = problem.deck?.cards ?? [];
  if (!cards.some((card) => card.id === o.cardId)) {
    return json({ error: `unknown card "${o.cardId}"` }, { status: 400 });
  }

  const outcome = await recordFlashcardReview({
    userId: locals.user!.id,
    problemId: `${params.trackSlug}/${params.problemSlug}`,
    cardId: o.cardId,
    grade: o.grade,
    responseMs: typeof o.responseMs === 'number' ? o.responseMs : 0,
    cardIds: cards.map((card) => card.id)
  });

  return json(outcome);
};
