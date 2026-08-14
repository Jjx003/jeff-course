import { error, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { getCompletionsForTrack } from '$lib/server/stats';
import { enrollInTrack, isEnrolled } from '$lib/server/enrollments';

export const load: PageServerLoad = async ({ locals, params }) => {
  const track = await localCourseRepository.getTrack(params.trackSlug);
  if (!track) {
    error(404, `Track "${params.trackSlug}" not found`);
  }
  const [completions, enrolled] = await Promise.all([
    getCompletionsForTrack(locals.user!.id, params.trackSlug),
    isEnrolled(locals.user!.id, params.trackSlug)
  ]);
  return { track, completions, enrolled };
};

export const actions: Actions = {
  enroll: async ({ locals, params }) => {
    const track = await localCourseRepository.getTrack(params.trackSlug);
    if (!track) return fail(404, { message: 'Course not found.' });
    await enrollInTrack(locals.user!.id, params.trackSlug);
    return { enrolled: true };
  }
};
