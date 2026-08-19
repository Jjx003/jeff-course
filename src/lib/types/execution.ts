/**
 * Types for code execution, run snapshots, and submission history.
 *
 * The `ExecutionService` interface accepts a `RunRequest` and returns a
 * `RunResult`. Local implementations mock this; future remote implementations
 * will call a sandboxed execution API with the same contract.
 */

import type { Language } from './course.js';

// ── Execution request / result ───────────────────────────────────────────

export interface RunRequest {
  problemId: string;  // "{trackSlug}/{problemSlug}"
  language: Language;
  code: string;
}

/**
 * One chunk of program output, tagged with the stream it came from.
 *
 * The Output panel replays these in arrival order so interleaved
 * stdout/stderr reads the same way it would in a terminal. `stdout` and
 * `stderr` on RunResult remain the concatenated-per-stream view (used for
 * grading, the tutor, and older persisted rows that predate this field).
 */
export interface LogLine {
  stream: 'stdout' | 'stderr';
  text: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  /**
   * Chronological interleave of stdout/stderr chunks. Optional: rows written
   * before this field existed only have the split streams.
   */
  log?: LogLine[];
  /** Wall-clock ms, or null if not available. */
  durationMs: number | null;
  /** Whether execution finished without a runtime error. */
  success: boolean;
  /** Human-readable status label shown in the UI. */
  status: 'ok' | 'error' | 'timeout' | 'cancelled';
  /** Process exit code, when the runner reported one. */
  exitCode?: number | null;
}

export interface SubmitRequest {
  problemId: string;
  language: Language;
  code: string;
}

/** A single row of the expected-vs-actual comparison. */
export interface DiffRow {
  /**
   * `same`    — both sides agree (exactly, or within numeric tolerance)
   * `changed` — both sides have a line here and they differ
   * `missing` — expected has a line, actual ran out / dropped it
   * `extra`   — actual printed a line expected did not have
   */
  kind: 'same' | 'changed' | 'missing' | 'extra';
  expected?: string;
  actual?: string;
  /** 1-based line numbers within each side, when that side has a line. */
  expectedNo?: number;
  actualNo?: number;
}

export interface SubmitResult {
  verdict: 'accepted' | 'wrong_answer' | 'error' | 'pending';
  /**
   * Raw grader message. For wrong answers this historically carried the
   * unified diff appended after a blank line; prefer `summary` + `diff`.
   */
  message: string;
  /** Score in [0, 100], or null for non-graded problems. */
  score: number | null;
  /** One-line, human-readable headline. Never contains a diff dump. */
  summary?: string;
  /** Structured comparison, present on `wrong_answer`. */
  diff?: DiffRow[];
  /** Reconstructed full texts, for the side-by-side view and copy buttons. */
  expectedText?: string;
  actualText?: string;
  /** Captured stderr, present on `error` verdicts. */
  stderr?: string;
  /** @deprecated Kept so submissions saved by older builds still render. */
  testResults?: TestCaseResult[];
}

export interface TestCaseResult {
  name: string;
  passed: boolean;
  expected?: string;
  actual?: string;
  durationMs?: number;
}

// ── Persisted snapshot types ─────────────────────────────────────────────

/**
 * A snapshot saved every time the user clicks "Run".
 * Immutable after creation.
 */
export interface RunSnapshot {
  id: string;
  problemId: string;
  language: Language;
  code: string;
  result: RunResult;
  timestamp: number; // Unix ms
}

/**
 * A snapshot saved every time the user clicks "Submit".
 * Immutable after creation.
 */
export interface SubmitSnapshot {
  id: string;
  problemId: string;
  language: Language;
  code: string;
  result: SubmitResult;
  timestamp: number; // Unix ms
}

// ── Draft type ───────────────────────────────────────────────────────────

/**
 * The user's current working draft for a (problem, language) pair.
 * Updated on every keystroke (debounced).
 */
export interface Draft {
  problemId: string;
  language: Language;
  code: string;
  lastSavedAt: number; // Unix ms
}
