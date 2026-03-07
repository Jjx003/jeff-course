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

export interface RunResult {
  stdout: string;
  stderr: string;
  /** Wall-clock ms, or null if not available. */
  durationMs: number | null;
  /** Whether execution finished without a runtime error. */
  success: boolean;
  /** Human-readable status label shown in the UI. */
  status: 'ok' | 'error' | 'timeout';
}

export interface SubmitRequest {
  problemId: string;
  language: Language;
  code: string;
}

export interface SubmitResult {
  verdict: 'accepted' | 'wrong_answer' | 'error' | 'pending';
  message: string;
  /** Score in [0, 100], or null for non-graded problems. */
  score: number | null;
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
