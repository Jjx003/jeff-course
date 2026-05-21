import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local.js';
import { getReadingAudioManifest } from '$lib/server/readingAudio.js';

export const GET: RequestHandler = async ({ params }) => {
  const problem = await localCourseRepository.getProblem(params.trackSlug, params.problemSlug);
  if (!problem) error(404, 'Problem not found');
  if (problem.type !== 'reading') return json({ available: false, title: null, clips: [] });

  return json(await getReadingAudioManifest(params.trackSlug, problem));
};
