/**
 * Study-time helpers — server side.
 *
 * Tracks the time the user actively spends on a problem page. The client
 * owns `active_ms` as a running counter (paused on idle / hidden tab); each
 * heartbeat overwrites the row's `active_ms` rather than appending a delta,
 * which keeps the math simple and recovery-friendly even if heartbeats are
 * lost in transit.
 *
 * SERVER-SIDE ONLY. Never import from a component or client-side file.
 */

import { dbReady, dbAll, dbRun } from './db.js';
import { loadAllTracks } from '$lib/content/courseLoader.js';
import { toLocalDateKey } from './stats.js';

// Sane upper bound for a single session: 24 hours. Anything larger is almost
// certainly a clock or client bug; we reject it at the API edge.
export const MAX_SESSION_MS = 24 * 60 * 60 * 1000;

type SessionRow = {
  id: string;
  problem_id: string;
  started_at: number;
  active_ms: number;
};

/**
 * Insert or update the heartbeat row for `sessionId`. `activeMs` is the
 * client's running total — we overwrite, not accumulate, so a duplicated or
 * out-of-order heartbeat can't double-count.
 */
export async function upsertHeartbeat(
  userId: string,
  sessionId: string,
  problemId: string,
  activeMs: number,
  startedAt: number
): Promise<void> {
  await dbReady;
  const now = Date.now();
  await dbRun(
    `INSERT INTO study_sessions (id, user_id, problem_id, started_at, active_ms, last_heartbeat_at)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT (id)
     DO UPDATE SET active_ms = EXCLUDED.active_ms,
                   last_heartbeat_at = EXCLUDED.last_heartbeat_at`,
    [sessionId, userId, problemId, startedAt, activeMs, now]
  );
}

/**
 * Build the orphan-safe filter set: only sessions whose `problem_id` maps to
 * an actual current course module are counted. This keeps stats robust
 * against renamed or removed content.
 */
async function knownProblemIdSet(): Promise<Set<string>> {
  const tracks = await loadAllTracks();
  const set = new Set<string>();
  for (const t of tracks) {
    for (const p of t.problems) set.add(`${t.slug}/${p.slug}`);
  }
  return set;
}

/** Sum `active_ms` across every session that maps to a real problem. */
export async function getTotalActiveMs(userId: string): Promise<number> {
  await dbReady;
  const rows = await dbAll<SessionRow>(
    'SELECT id, problem_id, started_at, active_ms FROM study_sessions WHERE user_id = ?',
    [userId]
  );
  const known = await knownProblemIdSet();
  let total = 0;
  for (const r of rows) {
    if (!known.has(r.problem_id)) continue;
    total += Number(r.active_ms);
  }
  return total;
}

/**
 * Sum `active_ms` for sessions whose `started_at` falls on the given local
 * date key (YYYY-MM-DD). We bucket by `started_at` rather than
 * `last_heartbeat_at` so a long session that begins late at night counts
 * toward the day it began on, matching how streak / heatmap dates work.
 */
export async function getActiveMsForDateKey(userId: string, dateKey: string): Promise<number> {
  await dbReady;
  const rows = await dbAll<SessionRow>(
    'SELECT id, problem_id, started_at, active_ms FROM study_sessions WHERE user_id = ?',
    [userId]
  );
  const known = await knownProblemIdSet();
  let total = 0;
  for (const r of rows) {
    if (!known.has(r.problem_id)) continue;
    if (toLocalDateKey(Number(r.started_at)) !== dateKey) continue;
    total += Number(r.active_ms);
  }
  return total;
}

/** Bucketed view: local date → total active ms. */
export async function getActiveMsByDate(userId: string): Promise<Map<string, number>> {
  await dbReady;
  const rows = await dbAll<SessionRow>(
    'SELECT id, problem_id, started_at, active_ms FROM study_sessions WHERE user_id = ?',
    [userId]
  );
  const known = await knownProblemIdSet();
  const out = new Map<string, number>();
  for (const r of rows) {
    if (!known.has(r.problem_id)) continue;
    const key = toLocalDateKey(Number(r.started_at));
    out.set(key, (out.get(key) ?? 0) + Number(r.active_ms));
  }
  return out;
}
