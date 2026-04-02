/**
 * ApiSubmissionStorage
 *
 * Fetch-based submission storage backed by DuckDB on the server.
 * Only submissions with verdict = 'accepted' are persisted.
 */

import type { SubmissionStorage } from '../submissionStorage.js';
import type { SubmitSnapshot } from '$lib/types/execution.js';

export class ApiSubmissionStorage implements SubmissionStorage {
  async addSubmission(snapshot: SubmitSnapshot): Promise<void> {
    await fetch(`/api/submissions/${snapshot.problemId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(snapshot)
    });
  }

  async getSubmissions(problemId: string): Promise<SubmitSnapshot[]> {
    const res = await fetch(`/api/submissions/${problemId}`);
    const { submissions } = (await res.json()) as { submissions: SubmitSnapshot[] };
    return submissions;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async clearSubmissions(_problemId: string): Promise<void> {
    // Not implemented.
  }
}

export const apiSubmissionStorage = new ApiSubmissionStorage();
