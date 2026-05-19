/**
 * DuckDB singleton for server-side persistence.
 *
 * Stores:
 *   drafts      — one row per (problem_id, language), upserted on every auto-save
 *   runs        — one row per (problem_id, language), upserted on every Run click
 *   submissions — append-only, only accepted verdicts are inserted
 *
 * SERVER-SIDE ONLY. Never import from components or client-side code.
 */

// duckdb is a CJS native addon. Use createRequire so Vite's module runner
// doesn't intercept and mis-wrap it.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const _require = createRequire(import.meta.url);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const duckdb = _require('duckdb') as any;

const DB_PATH =
  process.env.DB_PATH ?? path.join(process.cwd(), 'data', 'jeff-course.duckdb');

// Ensure the data directory exists before DuckDB tries to open the file.
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

// Survive Vite HMR module reloads without opening multiple DB handles.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
if (!g.__duckdb) {
  g.__duckdb = new duckdb.Database(DB_PATH);
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const db: any = g.__duckdb;

// ── Promisified helpers ──────────────────────────────────────────────────────

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

// ── Schema init ──────────────────────────────────────────────────────────────

export const dbReady: Promise<void> = (async () => {
  await dbRun(`
    CREATE TABLE IF NOT EXISTS drafts (
      problem_id    VARCHAR NOT NULL,
      language      VARCHAR NOT NULL,
      code          TEXT    NOT NULL,
      last_saved_at BIGINT  NOT NULL,
      PRIMARY KEY (problem_id, language)
    )
  `);

  await dbRun(`
    CREATE TABLE IF NOT EXISTS runs (
      problem_id VARCHAR NOT NULL,
      language   VARCHAR NOT NULL,
      id         VARCHAR NOT NULL,
      code       TEXT    NOT NULL,
      result     VARCHAR NOT NULL,
      timestamp  BIGINT  NOT NULL,
      PRIMARY KEY (problem_id, language)
    )
  `);

  await dbRun(`
    CREATE TABLE IF NOT EXISTS submissions (
      id         VARCHAR PRIMARY KEY,
      problem_id VARCHAR NOT NULL,
      language   VARCHAR NOT NULL,
      code       TEXT    NOT NULL,
      result     VARCHAR NOT NULL,
      timestamp  BIGINT  NOT NULL
    )
  `);

  // ── Gamification ──────────────────────────────────────────────────────
  // Reading modules don't produce submissions, so we track their completion
  // explicitly. One row per problem; first mark-complete is preserved.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS reading_completions (
      problem_id   VARCHAR PRIMARY KEY,
      completed_at BIGINT  NOT NULL
    )
  `);

  // Achievements are persisted on first unlock so we can show a stable
  // "earned on" date in the UI. Locked achievements are NOT stored — they
  // are computed on demand from the static definition list.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS achievements (
      id          VARCHAR PRIMARY KEY,
      unlocked_at BIGINT  NOT NULL
    )
  `);

  // Quiz attempts are append-only. Each row is one completed pass through
  // a quiz module (the user clicked through every question to "See results").
  // The "first passing attempt" is what flips `reading_completions` for a
  // quiz module — it's the moment a quiz is considered complete and grants
  // its 5 points. Below-threshold attempts are still recorded so the intro
  // screen can show "Best: X/Y" and the attempt counter.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS quiz_attempts (
      id           VARCHAR PRIMARY KEY,
      problem_id   VARCHAR NOT NULL,
      total        INTEGER NOT NULL,
      correct      INTEGER NOT NULL,
      passed       BOOLEAN NOT NULL,
      duration_ms  BIGINT  NOT NULL,
      completed_at BIGINT  NOT NULL
    )
  `);
  await dbRun(`CREATE INDEX IF NOT EXISTS quiz_attempts_problem_idx ON quiz_attempts (problem_id)`);

  // Study sessions track active engagement time per problem visit. The
  // client owns `active_ms` as a running counter (it pauses on idle / hidden
  // tab); each heartbeat overwrites the row's `active_ms`, never appends to
  // it. `started_at` is fixed at session creation and is what we bucket by
  // for "time today" calculations.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS study_sessions (
      id                VARCHAR PRIMARY KEY,
      problem_id        VARCHAR NOT NULL,
      started_at        BIGINT  NOT NULL,
      active_ms         BIGINT  NOT NULL,
      last_heartbeat_at BIGINT  NOT NULL
    )
  `);

  // ── Sandbox (containerized / baremetal code execution) ────────────────
  //
  // One row per Run/Submit click that goes through the sandbox pipeline.
  // Persisted so the /sessions page can show history across restarts and
  // so the boot-time zombie reaper can find stale rows to mark crashed.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS sandbox_sessions (
      id              VARCHAR PRIMARY KEY,
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
  `);

  await dbRun(`CREATE INDEX IF NOT EXISTS sandbox_sessions_status_idx ON sandbox_sessions (status)`);
  await dbRun(`CREATE INDEX IF NOT EXISTS sandbox_sessions_started_idx ON sandbox_sessions (started_at)`);

  // Per-track preference for sandbox mode + resources. Sticky between visits.
  await dbRun(`
    CREATE TABLE IF NOT EXISTS sandbox_preferences (
      track_slug      VARCHAR PRIMARY KEY,
      preferred_mode  VARCHAR NOT NULL,
      resources_json  TEXT    NOT NULL,
      updated_at      BIGINT  NOT NULL
    )
  `);
})();
