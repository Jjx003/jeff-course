/**
 * CourseRepository interface.
 *
 * Abstracts the source of course content. The local implementation reads from
 * the filesystem via courseLoader. A future remote implementation would call
 * a CMS API or database.
 *
 * UI components and route load functions depend only on this interface —
 * never on a concrete implementation directly.
 */

import type { Track, Problem } from '$lib/types/course.js';

export interface CourseRepository {
  /** Return all available tracks, sorted by order. */
  getAllTracks(): Promise<Track[]>;

  /** Return a single track with its problem list, or null if not found. */
  getTrack(trackSlug: string): Promise<Track | null>;

  /** Return full problem data (tabs, starter code, navigation), or null. */
  getProblem(trackSlug: string, problemSlug: string): Promise<Problem | null>;
}
