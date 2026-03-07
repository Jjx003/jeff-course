import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';

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

  return { track, problem, prevProblem, nextProblem };
};
