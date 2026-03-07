/**
 * RunHistoryStorage interface.
 *
 * Persists run snapshots (timestamp, code, result) for each problem.
 * Appended on every "Run" click.
 *
 * Local implementation: localStorage.
 * Future remote implementation: POST /api/runs
 */

import type { RunSnapshot } from '$lib/types/execution.js';

export interface RunHistoryStorage {
  /** Append a new run snapshot. */
  addRun(snapshot: RunSnapshot): Promise<void>;

  /** Return all run snapshots for a problem, newest first. */
  getRuns(problemId: string): Promise<RunSnapshot[]>;

  /** Clear run history for a problem. */
  clearRuns(problemId: string): Promise<void>;
}
