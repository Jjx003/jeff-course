/**
 * SubmissionStorage interface.
 *
 * Persists submit snapshots for each problem.
 * Appended on every "Submit" click.
 *
 * Local implementation: localStorage.
 * Future remote implementation: POST /api/submissions
 */

import type { SubmitSnapshot } from '$lib/types/execution.js';

export interface SubmissionStorage {
  /** Append a new submission snapshot. */
  addSubmission(snapshot: SubmitSnapshot): Promise<void>;

  /** Return all submission snapshots for a problem, newest first. */
  getSubmissions(problemId: string): Promise<SubmitSnapshot[]>;

  /** Clear submission history for a problem. */
  clearSubmissions(problemId: string): Promise<void>;
}
