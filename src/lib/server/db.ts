/**
 * DuckDB singleton for server-side persistence.
 *
 * SERVER-SIDE ONLY. Never import from components or client-side code.
 */

import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const _require = createRequire(import.meta.url);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const duckdb = _require('duckdb') as any;

const DB_PATH =
  process.env.DB_PATH ?? path.join(process.cwd(), 'data', 'jeff-course.duckdb');

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

// Survive Vite HMR module reloads without opening multiple DB handles.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
if (!g.__duckdb) {
  g.__duckdb = new duckdb.Database(DB_PATH);
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const db: any = g.__duckdb;

export function dbRun(sql: string, params: unknown[] = []): Promise<void> {
  return new Promise((resolve, reject) => {
    db.run(sql, ...params, (err: Error | null) => {
      if (err) reject(err);
      else resolve();
    });
  });
}

export function dbAll<T = Record<string, unknown>>(
  sql: string,
  params: unknown[] = []
): Promise<T[]> {
  return new Promise((resolve, reject) => {
    db.all(sql, ...params, (err: Error | null, rows: T[]) => {
      if (err) reject(err);
      else resolve(rows ?? []);
    });
  });
}

async function tableColumns(table: string): Promise<Set<string>> {
  const rows = await dbAll<{ name: string }>(
    `SELECT column_name AS name
       FROM information_schema.columns
      WHERE table_name = ?`,
    [table]
  );
  return new Set(rows.map((row) => row.name));
}

async function migrateTableToUserScoped(
  table: string,
  createSql: string,
  copySql: string
): Promise<void> {
  const columns = await tableColumns(table);
  if (columns.size === 0) {
    await dbRun(createSql);
    return;
  }
  if (columns.has('user_id')) return;

  const indexes = await dbAll<{ index_name: string }>(
    'SELECT index_name FROM duckdb_indexes() WHERE table_name = ?',
    [table]
  );
  for (const index of indexes) {
    await dbRun(`DROP INDEX IF EXISTS "${index.index_name.replaceAll('"', '""')}"`);
  }

  const old = `${table}_single_user_backup`;
  await dbRun(`ALTER TABLE ${table} RENAME TO ${old}`);
  await dbRun(createSql);
  await dbRun(copySql.replaceAll('__OLD__', old));
  await dbRun(`DROP TABLE ${old}`);
}

export const dbReady: Promise<void> = (async () => {
  await dbRun(`
    CREATE TABLE IF NOT EXISTS users (
      id            VARCHAR PRIMARY KEY,
      name          VARCHAR NOT NULL UNIQUE,
      role          VARCHAR NOT NULL,
      password_hash TEXT    NOT NULL,
      created_at    BIGINT  NOT NULL,
      last_login_at BIGINT
    )
  `);

  await dbRun(`
    CREATE TABLE IF NOT EXISTS auth_sessions (
      id         VARCHAR PRIMARY KEY,
      user_id    VARCHAR NOT NULL,
      created_at BIGINT  NOT NULL,
      expires_at BIGINT  NOT NULL
    )
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS auth_sessions_user_idx ON auth_sessions (user_id)`);
  await dbRun(`DELETE FROM auth_sessions WHERE expires_at <= ?`, [Date.now()]);

  await dbRun(`
    CREATE TABLE IF NOT EXISTS course_enrollments (
      user_id    VARCHAR NOT NULL,
      track_slug VARCHAR NOT NULL,
      enrolled_at BIGINT NOT NULL,
      PRIMARY KEY (user_id, track_slug)
    )
  `);

  await migrateTableToUserScoped('drafts', `
    CREATE TABLE IF NOT EXISTS drafts (
      user_id       VARCHAR NOT NULL,
      problem_id    VARCHAR NOT NULL,
      language      VARCHAR NOT NULL,
      code          TEXT    NOT NULL,
      last_saved_at BIGINT  NOT NULL,
      PRIMARY KEY (user_id, problem_id, language)
    )
  `, `
    INSERT INTO drafts (user_id, problem_id, language, code, last_saved_at)
    SELECT 'local', problem_id, language, code, last_saved_at FROM __OLD__
  `);

  await migrateTableToUserScoped('runs', `
    CREATE TABLE IF NOT EXISTS runs (
      user_id    VARCHAR NOT NULL,
      problem_id VARCHAR NOT NULL,
      language   VARCHAR NOT NULL,
      id         VARCHAR NOT NULL,
      code       TEXT    NOT NULL,
      result     VARCHAR NOT NULL,
      timestamp  BIGINT  NOT NULL,
      PRIMARY KEY (user_id, problem_id, language)
    )
  `, `
    INSERT INTO runs (user_id, problem_id, language, id, code, result, timestamp)
    SELECT 'local', problem_id, language, id, code, result, timestamp FROM __OLD__
  `);

  await migrateTableToUserScoped('submissions', `
    CREATE TABLE IF NOT EXISTS submissions (
      id         VARCHAR PRIMARY KEY,
      user_id    VARCHAR NOT NULL,
      problem_id VARCHAR NOT NULL,
      language   VARCHAR NOT NULL,
      code       TEXT    NOT NULL,
      result     VARCHAR NOT NULL,
      timestamp  BIGINT  NOT NULL
    )
  `, `
    INSERT INTO submissions (id, user_id, problem_id, language, code, result, timestamp)
    SELECT id, 'local', problem_id, language, code, result, timestamp FROM __OLD__
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS submissions_user_problem_idx ON submissions (user_id, problem_id)`);

  await migrateTableToUserScoped('reading_completions', `
    CREATE TABLE IF NOT EXISTS reading_completions (
      user_id      VARCHAR NOT NULL,
      problem_id   VARCHAR NOT NULL,
      completed_at BIGINT  NOT NULL,
      PRIMARY KEY (user_id, problem_id)
    )
  `, `
    INSERT INTO reading_completions (user_id, problem_id, completed_at)
    SELECT 'local', problem_id, completed_at FROM __OLD__
  `);

  await migrateTableToUserScoped('achievements', `
    CREATE TABLE IF NOT EXISTS achievements (
      user_id     VARCHAR NOT NULL,
      id          VARCHAR NOT NULL,
      unlocked_at BIGINT  NOT NULL,
      PRIMARY KEY (user_id, id)
    )
  `, `
    INSERT INTO achievements (user_id, id, unlocked_at)
    SELECT 'local', id, unlocked_at FROM __OLD__
  `);

  await migrateTableToUserScoped('quiz_attempts', `
    CREATE TABLE IF NOT EXISTS quiz_attempts (
      id           VARCHAR PRIMARY KEY,
      user_id      VARCHAR NOT NULL,
      problem_id   VARCHAR NOT NULL,
      total        INTEGER NOT NULL,
      correct      INTEGER NOT NULL,
      passed       BOOLEAN NOT NULL,
      duration_ms  BIGINT  NOT NULL,
      completed_at BIGINT  NOT NULL
    )
  `, `
    INSERT INTO quiz_attempts (id, user_id, problem_id, total, correct, passed, duration_ms, completed_at)
    SELECT id, 'local', problem_id, total, correct, passed, duration_ms, completed_at FROM __OLD__
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS quiz_attempts_problem_idx ON quiz_attempts (user_id, problem_id)`);

  await migrateTableToUserScoped('drill_attempts', `
    CREATE TABLE IF NOT EXISTS drill_attempts (
      id           VARCHAR PRIMARY KEY,
      user_id      VARCHAR NOT NULL,
      problem_id   VARCHAR NOT NULL,
      total        INTEGER NOT NULL,
      correct      INTEGER NOT NULL,
      avg_ms       BIGINT  NOT NULL,
      best_streak  INTEGER NOT NULL,
      duration_ms  BIGINT  NOT NULL,
      completed_at BIGINT  NOT NULL
    )
  `, `
    INSERT INTO drill_attempts (id, user_id, problem_id, total, correct, avg_ms, best_streak, duration_ms, completed_at)
    SELECT id, 'local', problem_id, total, correct, avg_ms, best_streak, duration_ms, completed_at FROM __OLD__
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS drill_attempts_problem_idx ON drill_attempts (user_id, problem_id)`);

  await migrateTableToUserScoped('study_sessions', `
    CREATE TABLE IF NOT EXISTS study_sessions (
      id                VARCHAR PRIMARY KEY,
      user_id           VARCHAR NOT NULL,
      problem_id        VARCHAR NOT NULL,
      started_at        BIGINT  NOT NULL,
      active_ms         BIGINT  NOT NULL,
      last_heartbeat_at BIGINT  NOT NULL
    )
  `, `
    INSERT INTO study_sessions (id, user_id, problem_id, started_at, active_ms, last_heartbeat_at)
    SELECT id, 'local', problem_id, started_at, active_ms, last_heartbeat_at FROM __OLD__
  `);

  await migrateTableToUserScoped('sandbox_sessions', `
    CREATE TABLE IF NOT EXISTS sandbox_sessions (
      id              VARCHAR PRIMARY KEY,
      user_id         VARCHAR NOT NULL,
      problem_id      VARCHAR NOT NULL,
      language        VARCHAR NOT NULL,
      action          VARCHAR NOT NULL,
      mode            VARCHAR NOT NULL,
      status          VARCHAR NOT NULL,
      container_name  VARCHAR,
      host_pid        INTEGER,
      started_at      BIGINT  NOT NULL,
      completed_at    BIGINT,
      exit_code       INTEGER,
      error_message   TEXT,
      resources_json  TEXT    NOT NULL,
      stdout_bytes    BIGINT  NOT NULL DEFAULT 0,
      stderr_bytes    BIGINT  NOT NULL DEFAULT 0,
      submit_verdict  VARCHAR,
      submit_message  TEXT,
      submit_score    INTEGER
    )
  `, `
    INSERT INTO sandbox_sessions
      (id, user_id, problem_id, language, action, mode, status,
       container_name, host_pid, started_at, completed_at, exit_code,
       error_message, resources_json, stdout_bytes, stderr_bytes,
       submit_verdict, submit_message, submit_score)
    SELECT id, 'local', problem_id, language, action, mode, status,
       container_name, host_pid, started_at, completed_at, exit_code,
       error_message, resources_json, stdout_bytes, stderr_bytes,
       submit_verdict, submit_message, submit_score
    FROM __OLD__
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS sandbox_sessions_status_idx ON sandbox_sessions (user_id, status)`);
  await dbRun(`CREATE INDEX IF NOT EXISTS sandbox_sessions_started_idx ON sandbox_sessions (user_id, started_at)`);

  await migrateTableToUserScoped('sandbox_preferences', `
    CREATE TABLE IF NOT EXISTS sandbox_preferences (
      user_id         VARCHAR NOT NULL,
      track_slug      VARCHAR NOT NULL,
      preferred_mode  VARCHAR NOT NULL,
      resources_json  TEXT    NOT NULL,
      updated_at      BIGINT  NOT NULL,
      PRIMARY KEY (user_id, track_slug)
    )
  `, `
    INSERT INTO sandbox_preferences (user_id, track_slug, preferred_mode, resources_json, updated_at)
    SELECT 'local', track_slug, preferred_mode, resources_json, updated_at FROM __OLD__
  `);

  await dbRun(`
    CREATE TABLE IF NOT EXISTS tutor_messages (
      id         VARCHAR PRIMARY KEY,
      user_id    VARCHAR NOT NULL,
      problem_id VARCHAR NOT NULL,
      role       VARCHAR NOT NULL,
      content    TEXT    NOT NULL,
      created_at BIGINT  NOT NULL
    )
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS tutor_messages_thread_idx ON tutor_messages (user_id, problem_id, created_at)`);
  // Tool activity for assistant turns, stored as a JSON array. Added after
  // the table shipped, so existing local databases need the column grafted on.
  await dbRun(`ALTER TABLE tutor_messages ADD COLUMN IF NOT EXISTS steps TEXT`);

  // Preserve existing learners' work by enrolling courses that already have
  // progress. The conflict clause keeps this idempotent on later startups.
  await dbRun(`
    INSERT INTO course_enrollments (user_id, track_slug, enrolled_at)
    SELECT user_id, split_part(problem_id, '/', 1), MIN(activity_at)
    FROM (
      SELECT user_id, problem_id, timestamp AS activity_at FROM submissions
      UNION ALL SELECT user_id, problem_id, completed_at FROM reading_completions
      UNION ALL SELECT user_id, problem_id, completed_at FROM quiz_attempts
      UNION ALL SELECT user_id, problem_id, completed_at FROM drill_attempts
      UNION ALL SELECT user_id, problem_id, started_at FROM study_sessions
    ) activity
    WHERE problem_id LIKE '%/%'
    GROUP BY user_id, split_part(problem_id, '/', 1)
    ON CONFLICT (user_id, track_slug) DO NOTHING
  `);
})();
