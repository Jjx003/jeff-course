/**
 * LocalCourseRepository
 *
 * Reads course content from the local filesystem via courseLoader.
 * This is the server-side implementation — it must only be instantiated
 * in server load functions (+page.server.ts), never in client components.
 *
 * Future: RemoteCourseRepository would call an HTTP API instead.
 */

import type { CourseRepository } from '../courseRepository.js';
import type { Track, Problem } from '$lib/types/course.js';
import { loadAllTracks, loadTrack, loadProblem } from '$lib/content/courseLoader.js';

export class LocalCourseRepository implements CourseRepository {
  async getAllTracks(): Promise<Track[]> {
    return loadAllTracks();
  }

  async getTrack(trackSlug: string): Promise<Track | null> {
    return loadTrack(trackSlug);
  }

  async getProblem(trackSlug: string, problemSlug: string): Promise<Problem | null> {
    return loadProblem(trackSlug, problemSlug);
  }
}

// Singleton — one instance for the lifetime of the server process.
export const localCourseRepository = new LocalCourseRepository();
