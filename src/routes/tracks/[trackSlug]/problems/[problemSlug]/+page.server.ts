import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { isReadingCompleted, isProblemCompleted, getQuizProgress, getDrillProgress } from '$lib/server/stats';
import { getDeckProgress } from '$lib/server/flashcards';
import { isEnrolled } from '$lib/server/enrollments';

export const load: PageServerLoad = async ({ locals, params }) => {
  if (!(await isEnrolled(locals.user!.id, params.trackSlug))) {
    redirect(303, `/tracks/${params.trackSlug}`);
  }
  const [track, problem] = await Promise.all([
    localCourseRepository.getTrack(params.trackSlug),
    localCourseRepository.getProblem(params.trackSlug, params.problemSlug)
  ]);

  if (!track) {
    error(404, `Track "${params.trackSlug}" not found`);
  }
  if (!problem) {
    error(404, `Problem "${params.problemSlug}" not found in track "${params.trackSlug}"`);
  }

  // Resolve prev/next ProblemMeta for navigation
  const prevProblem = problem.prevSlug
    ? track.problems.find((p) => p.slug === problem.prevSlug) ?? null
    : null;
  const nextProblem = problem.nextSlug
    ? track.problems.find((p) => p.slug === problem.nextSlug) ?? null
    : null;

  // Initial completion state. Avoids a flash of the "not completed" UI on
  // first render. The client re-checks via the API after hydration.
  const problemId = `${params.trackSlug}/${params.problemSlug}`;
  const initiallyCompleted =
    problem.type !== 'coding'
      ? await isReadingCompleted(locals.user!.id, problemId)
      : await isProblemCompleted(locals.user!.id, problemId);

  // For quiz/test modules, also seed the aggregate progress so the intro screen
  // can show "Best: X/Y" / "Passed" without a fetch on first paint.
  const initialQuizProgress =
    problem.type === 'quiz' || problem.type === 'test' ? await getQuizProgress(locals.user!.id, problemId) : null;
  const initialDrillProgress =
    problem.type === 'drill' ? await getDrillProgress(locals.user!.id, problemId, problem.drill?.targetAccuracy) : null;
  const initialFlashcardProgress =
    problem.type === 'flashcards'
      ? await getDeckProgress(
          locals.user!.id,
          problemId,
          (problem.deck?.cards ?? []).map((card) => card.id)
        )
      : null;

  return {
    track,
    problem,
    prevProblem,
    nextProblem,
    initiallyCompleted,
    initialQuizProgress,
    initialDrillProgress,
    initialFlashcardProgress
  };
};
