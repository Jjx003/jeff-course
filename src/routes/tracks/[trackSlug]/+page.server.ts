import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { getCompletionsForTrack } from '$lib/server/stats';

export const load: PageServerLoad = async ({ locals, params }) => {
  const track = await localCourseRepository.getTrack(params.trackSlug);
  if (!track) {
    error(404, `Track "${params.trackSlug}" not found`);
  }
  const completions = await getCompletionsForTrack(locals.user!.id, params.trackSlug);
  return { track, completions };
};
