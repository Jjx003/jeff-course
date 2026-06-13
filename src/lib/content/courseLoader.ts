/**
 * courseLoader.ts
 *
 * Thin facade over `courseParser.ts` that resolves visible course roots and
 * exposes the functions used by server load functions.
 *
 * Built-in courses come from `COURSES_DIR` or `<cwd>/courses`. Enabled course
 * packs from `data/course-packs.yaml` are appended after that.
 *
 * SERVER-SIDE ONLY.
 */

import { parseAllTracksFromRoots, parseTrack, parseFullProblem, resolveModulePath, resolveTrackPath } from './courseParser.js';
import { getCourseRoots } from './coursePackRegistry.js';
import type { Track, Problem } from '$lib/types/course.js';

function findRootForTrack(trackSlug: string): string | null {
  for (const root of getCourseRoots()) {
    if (resolveTrackPath(root, trackSlug)) return root;
  }
  return null;
}

/** Return all tracks, sorted by order. */
export function loadAllTracks(): Track[] {
  return parseAllTracksFromRoots(getCourseRoots());
}

/** Return a single track (with ProblemMeta list) by slug, or null. */
export function loadTrack(trackSlug: string): Track | null {
  const coursesDir = findRootForTrack(trackSlug);
  if (!coursesDir) return null;
  const trackPath = resolveTrackPath(coursesDir, trackSlug);
  if (!trackPath) return null;
  return parseTrack(trackPath);
}

/** Return full problem data (including markdown tabs + starter code) or null. */
export function loadProblem(trackSlug: string, problemSlug: string): Problem | null {
  const coursesDir = findRootForTrack(trackSlug);
  if (!coursesDir) return null;
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
