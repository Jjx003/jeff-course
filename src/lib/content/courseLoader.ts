/**
 * courseLoader.ts
 *
 * Thin facade over `courseParser.ts` that resolves the courses directory
 * path and exposes the functions used by server load functions.
 *
 * The `COURSES_DIR` env var allows overriding the default path, which makes
 * it easy to point a production deployment at a different content directory
 * without changing any application code.
 *
 * SERVER-SIDE ONLY.
 */

import path from 'path';
import { parseAllTracks, parseTrack, parseFullProblem, resolveModulePath } from './courseParser.js';
import type { Track, Problem } from '$lib/types/course.js';

function getCoursesDir(): string {
  // EXTENSION POINT: set COURSES_DIR env var in production to override.
  return process.env.COURSES_DIR ?? path.join(process.cwd(), 'courses');
}

/** Return all tracks, sorted by order. */
export function loadAllTracks(): Track[] {
  return parseAllTracks(getCoursesDir());
}

/** Return a single track (with ProblemMeta list) by slug, or null. */
export function loadTrack(trackSlug: string): Track | null {
  const coursesDir = getCoursesDir();
  const trackPath = path.join(coursesDir, trackSlug);
  return parseTrack(trackPath);
}

/** Return full problem data (including markdown tabs + starter code) or null. */
export function loadProblem(trackSlug: string, problemSlug: string): Problem | null {
  const coursesDir = getCoursesDir();
  const modulePath = resolveModulePath(coursesDir, trackSlug, problemSlug);
  if (!modulePath) return null;

  // Determine sibling problem slugs for prev/next navigation.
  const track = loadTrack(trackSlug);
  if (!track) return null;

  const problems = track.problems;
  const idx = problems.findIndex((p) => p.slug === problemSlug);
  const prevSlug = idx > 0 ? problems[idx - 1].slug : null;
  const nextSlug = idx < problems.length - 1 ? problems[idx + 1].slug : null;

  return parseFullProblem(modulePath, trackSlug, idx + 1, prevSlug, nextSlug);
}
