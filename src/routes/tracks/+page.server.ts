import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local';
import { getStatsSummary } from '$lib/server/stats';
import {
  enrollInTrack,
  getEnrolledTrackSlugs,
  unenrollFromTrack
} from '$lib/server/enrollments';

export const load: PageServerLoad = async ({ locals }) => {
  const tracks = await localCourseRepository.getAllTracks();
  const [stats, enrolledSlugs] = await Promise.all([
    getStatsSummary(locals.user!.id),
    getEnrolledTrackSlugs(locals.user!.id)
  ]);
  // Provide a quick lookup of per-track progress (slug → {completed, total}).
  const progressBySlug = Object.fromEntries(
    stats.trackProgress.map((t) => [t.slug, { completed: t.completed, total: t.total }])
  );
  return {
    enrolledTracks: tracks.filter((track) => enrolledSlugs.has(track.slug)),
    availableTracks: tracks.filter((track) => !enrolledSlugs.has(track.slug)),
    progressBySlug
  };
};

export const actions: Actions = {
  enroll: async ({ locals, request }) => {
    const form = await request.formData();
    const trackSlug = String(form.get('trackSlug') ?? '');
    const track = trackSlug ? await localCourseRepository.getTrack(trackSlug) : null;
    if (!track) return fail(404, { message: 'Course not found.' });
    await enrollInTrack(locals.user!.id, trackSlug);
    return { enrolled: trackSlug };
  },
  unenroll: async ({ locals, request }) => {
    const form = await request.formData();
    const trackSlug = String(form.get('trackSlug') ?? '');
    const track = trackSlug ? await localCourseRepository.getTrack(trackSlug) : null;
    if (!track) return fail(404, { message: 'Course not found.' });
    await unenrollFromTrack(locals.user!.id, trackSlug);
    return { unenrolled: trackSlug };
  }
};
