import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';

export const load: PageServerLoad = async ({ params }) => {
  const track = await localCourseRepository.getTrack(params.trackSlug);
  if (!track) {
    error(404, `Track "${params.trackSlug}" not found`);
  }
  return { track };
};
