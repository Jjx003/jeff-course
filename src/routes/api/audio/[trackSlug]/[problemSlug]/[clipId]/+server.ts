import { error } from '@sveltejs/kit';
import { readFile } from 'node:fs/promises';
import type { RequestHandler } from './$types';
import { localCourseRepository } from '$lib/services/local/courseRepository.local.js';
import { getReadingAudioClipPath } from '$lib/server/readingAudio.js';

export const GET: RequestHandler = async ({ params }) => {
  const problem = await localCourseRepository.getProblem(params.trackSlug, params.problemSlug);
  if (!problem || problem.type !== 'reading') error(404, 'Audio clip not found');

  const file = await getReadingAudioClipPath(params.trackSlug, problem, params.clipId);
  if (!file) error(404, 'Audio clip not found');

  const bytes = await readFile(file);
  return new Response(bytes, {
    headers: {
      'content-type': 'audio/wav',
      'cache-control': 'private, max-age=3600'
    }
  });
};
