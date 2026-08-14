import { dbAll, dbReady, dbRun } from './db.js';

interface EnrollmentRow {
  track_slug: string;
}

export async function getEnrolledTrackSlugs(userId: string): Promise<Set<string>> {
  await dbReady;
  const rows = await dbAll<EnrollmentRow>(
    `SELECT track_slug FROM course_enrollments
     WHERE user_id = ? AND enrolled_at > 0
     ORDER BY enrolled_at`,
    [userId]
  );
  return new Set(rows.map((row) => row.track_slug));
}

export async function isEnrolled(userId: string, trackSlug: string): Promise<boolean> {
  await dbReady;
  const rows = await dbAll<{ enrolled: number }>(
    `SELECT 1 AS enrolled FROM course_enrollments
     WHERE user_id = ? AND track_slug = ? AND enrolled_at > 0
     LIMIT 1`,
    [userId, trackSlug]
  );
  return rows.length > 0;
}

export async function enrollInTrack(userId: string, trackSlug: string): Promise<void> {
  await dbReady;
  await dbRun(
    `INSERT INTO course_enrollments (user_id, track_slug, enrolled_at) VALUES (?, ?, ?)
     ON CONFLICT (user_id, track_slug) DO UPDATE SET enrolled_at = excluded.enrolled_at`,
    [userId, trackSlug, Date.now()]
  );
}

export async function unenrollFromTrack(userId: string, trackSlug: string): Promise<void> {
  await dbReady;
  // Keep an inactive marker so startup's progress backfill does not re-enroll paused courses.
  await dbRun(
    `INSERT INTO course_enrollments (user_id, track_slug, enrolled_at) VALUES (?, ?, 0)
     ON CONFLICT (user_id, track_slug) DO UPDATE SET enrolled_at = 0`,
    [userId, trackSlug]
  );
}
