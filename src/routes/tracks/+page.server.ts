import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';

export const load: PageServerLoad = async () => {
  const tracks = await localCourseRepository.getAllTracks();
  return { tracks };
};
