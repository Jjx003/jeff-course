import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { isReadingCompleted, isProblemCompleted, getQuizProgress } from '$lib/server/stats';

export const load: PageServerLoad = async ({ params }) => {
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
    problem.type === 'reading' || problem.type === 'quiz'
      ? await isReadingCompleted(problemId)
      : await isProblemCompleted(problemId);

  // For quiz modules, also seed the aggregate progress so the intro screen
  // can show "Best: X/Y" / "Passed" without a fetch on first paint.
  const initialQuizProgress =
    problem.type === 'quiz' ? await getQuizProgress(problemId) : null;

  return { track, problem, prevProblem, nextProblem, initiallyCompleted, initialQuizProgress };
};
