/**
 * Sandbox persistence — DuckDB CRUD for sessions and per-track preferences.
 *
 * SERVER-SIDE ONLY.
 */

import { dbAll, dbReady, dbRun } from '$lib/server/db.js';
import type {
  ResourceLimits,
  SandboxMode,
  SessionAction,
  SessionRecord,
  SessionStatus,
  TrackPreference
} from './types.js';
import { defaultResourcesFor } from './types.js';

// ── Row → record marshalling ─────────────────────────────────────────────

interface SessionRow {
  id: string;
  user_id: string;
  problem_id: string;
  language: string;
  action: string;
  mode: string;
  status: string;
  container_name: string | null;
  host_pid: number | null;
  started_at: bigint | number;
  completed_at: bigint | number | null;
  exit_code: number | null;
  error_message: string | null;
  resources_json: string;
  stdout_bytes: bigint | number;
  stderr_bytes: bigint | number;
  submit_verdict: string | null;
  submit_message: string | null;
  submit_score: number | null;
}

function num(n: bigint | number | null | undefined): number {
  if (n === null || n === undefined) return 0;
  return typeof n === 'bigint' ? Number(n) : n;
}

function numOrNull(n: bigint | number | null | undefined): number | null {
  if (n === null || n === undefined) return null;
  return typeof n === 'bigint' ? Number(n) : n;
}

function rowToRecord(row: SessionRow): SessionRecord {
  let resources: ResourceLimits;
  try {
    resources = JSON.parse(row.resources_json) as ResourceLimits;
  } catch {
    resources = defaultResourcesFor(row.mode as SandboxMode);
  }
  return {
    id: row.id,
    userId: row.user_id,
    problemId: row.problem_id,
    language: row.language as SessionRecord['language'],
    action: row.action as SessionAction,
    mode: row.mode as SandboxMode,
    status: row.status as SessionStatus,
    containerName: row.container_name,
    hostPid: row.host_pid,
    startedAt: num(row.started_at),
    completedAt: numOrNull(row.completed_at),
    exitCode: row.exit_code,
    errorMessage: row.error_message,
    resources,
    stdoutBytes: num(row.stdout_bytes),
    stderrBytes: num(row.stderr_bytes),
    submitVerdict: (row.submit_verdict as SessionRecord['submitVerdict']) ?? null,
    submitMessage: row.submit_message,
    submitScore: row.submit_score
  };
}

// ── Sessions CRUD ────────────────────────────────────────────────────────

export async function insertSession(rec: SessionRecord): Promise<void> {
  await dbReady;
  await dbRun(
    `INSERT INTO sandbox_sessions
       (id, user_id, problem_id, language, action, mode, status,
        container_name, host_pid, started_at, completed_at, exit_code,
        error_message, resources_json, stdout_bytes, stderr_bytes,
        submit_verdict, submit_message, submit_score)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      rec.id,
      rec.userId,
      rec.problemId,
      rec.language,
      rec.action,
      rec.mode,
      rec.status,
      rec.containerName,
      rec.hostPid,
      rec.startedAt,
      rec.completedAt,
      rec.exitCode,
      rec.errorMessage,
      JSON.stringify(rec.resources),
      rec.stdoutBytes,
      rec.stderrBytes,
      rec.submitVerdict ?? null,
      rec.submitMessage ?? null,
      rec.submitScore ?? null
    ]
  );
}

/**
 * Persist a partial update for an existing session.
 *
 * Only the columns present in `patch` are touched; this lets the registry
 * push frequent counter updates (stdout_bytes/stderr_bytes) without racing
 * with a status flip from a different code path.
 */
export async function updateSession(
  id: string,
  patch: Partial<SessionRecord>
): Promise<void> {
  await dbReady;
  const sets: string[] = [];
  const params: unknown[] = [];

  const push = (col: string, val: unknown) => {
    sets.push(`${col} = ?`);
    params.push(val);
  };

  if (patch.status !== undefined) push('status', patch.status);
  if (patch.containerName !== undefined) push('container_name', patch.containerName);
  if (patch.hostPid !== undefined) push('host_pid', patch.hostPid);
  if (patch.completedAt !== undefined) push('completed_at', patch.completedAt);
  if (patch.exitCode !== undefined) push('exit_code', patch.exitCode);
  if (patch.errorMessage !== undefined) push('error_message', patch.errorMessage);
  if (patch.resources !== undefined) push('resources_json', JSON.stringify(patch.resources));
  if (patch.stdoutBytes !== undefined) push('stdout_bytes', patch.stdoutBytes);
  if (patch.stderrBytes !== undefined) push('stderr_bytes', patch.stderrBytes);
  if (patch.mode !== undefined) push('mode', patch.mode);
  if (patch.submitVerdict !== undefined) push('submit_verdict', patch.submitVerdict);
  if (patch.submitMessage !== undefined) push('submit_message', patch.submitMessage);
  if (patch.submitScore !== undefined) push('submit_score', patch.submitScore);

  if (sets.length === 0) return;
  params.push(id);
  await dbRun(`UPDATE sandbox_sessions SET ${sets.join(', ')} WHERE id = ?`, params);
}

export async function getSessionById(userId: string, id: string): Promise<SessionRecord | null> {
  await dbReady;
  const rows = await dbAll<SessionRow>(`SELECT * FROM sandbox_sessions WHERE user_id = ? AND id = ?`, [userId, id]);
  if (rows.length === 0) return null;
  return rowToRecord(rows[0]);
}

export async function listSessionRecords(userId: string, opts: { activeOnly?: boolean; limit?: number } = {}): Promise<SessionRecord[]> {
  await dbReady;
  const limit = Math.max(1, Math.min(500, opts.limit ?? 100));
  let sql = `SELECT * FROM sandbox_sessions WHERE user_id = ?`;
  const params: unknown[] = [userId];
  if (opts.activeOnly) {
    sql += ` AND status IN ('queued','starting','running')`;
  }
  sql += ` ORDER BY started_at DESC LIMIT ${limit}`;
  const rows = await dbAll<SessionRow>(sql, params);
  return rows.map(rowToRecord);
}

export async function deleteSessionsOlderThan(thresholdMs: number): Promise<number> {
  await dbReady;
  await dbRun(
    `DELETE FROM sandbox_sessions
     WHERE status IN ('completed','cancelled','killed','failed','crashed')
       AND started_at < ?`,
    [thresholdMs]
  );
  return 0;
}

/**
 * On server boot, any session still flagged starting/running is a leftover
 * from a previous process. Mark them crashed so the UI doesn't show stale
 * progress and the queue doesn't try to drain them.
 */
export async function reapStaleSessionsOnBoot(): Promise<number> {
  await dbReady;
  const now = Date.now();
  const stale = await dbAll<SessionRow>(
    `SELECT * FROM sandbox_sessions WHERE status IN ('starting','running')`
  );
  if (stale.length === 0) return 0;
  await dbRun(
    `UPDATE sandbox_sessions
       SET status = 'crashed',
           completed_at = ?,
           error_message = COALESCE(error_message, 'Server restarted while running')
     WHERE status IN ('starting','running')`,
    [now]
  );
  return stale.length;
}

// ── Preferences CRUD ─────────────────────────────────────────────────────

interface PrefRow {
  user_id: string;
  track_slug: string;
  preferred_mode: string;
  resources_json: string;
}

export async function getPreference(userId: string, trackSlug: string): Promise<TrackPreference | null> {
  await dbReady;
  const rows = await dbAll<PrefRow>(
    `SELECT user_id, track_slug, preferred_mode, resources_json
       FROM sandbox_preferences WHERE user_id = ? AND track_slug = ?`,
    [userId, trackSlug]
  );
  if (rows.length === 0) return null;
  const row = rows[0];
  let resources: ResourceLimits;
  try {
    resources = JSON.parse(row.resources_json) as ResourceLimits;
  } catch {
    resources = defaultResourcesFor(row.preferred_mode as SandboxMode);
  }
  return {
    userId: row.user_id,
    trackSlug: row.track_slug,
    preferredMode: row.preferred_mode as SandboxMode,
    resources
  };
}

export async function upsertPreference(pref: TrackPreference): Promise<void> {
  await dbReady;
  const now = Date.now();
  // DuckDB supports ON CONFLICT (col) DO UPDATE in current versions.
  await dbRun(
    `INSERT INTO sandbox_preferences (user_id, track_slug, preferred_mode, resources_json, updated_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT (user_id, track_slug) DO UPDATE
       SET preferred_mode = excluded.preferred_mode,
           resources_json = excluded.resources_json,
           updated_at     = excluded.updated_at`,
    [pref.userId, pref.trackSlug, pref.preferredMode, JSON.stringify(pref.resources), now]
  );
}
