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
})();
