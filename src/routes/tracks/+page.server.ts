import type { PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { getStatsSummary } from '$lib/server/stats';

export const load: PageServerLoad = async ({ locals }) => {
  const tracks = await localCourseRepository.getAllTracks();
  const stats = await getStatsSummary(locals.user!.id);
  // Provide a quick lookup of per-track progress (slug → {completed, total}).
  const progressBySlug = Object.fromEntries(
    stats.trackProgress.map((t) => [t.slug, { completed: t.completed, total: t.total }])
  );
  return { tracks, progressBySlug };
};
