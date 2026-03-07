/**
 * LocalSubmissionStorage
 *
 * Persists submission snapshots in localStorage.
 * Key pattern: `submissions::{problemId}`
 * Value: JSON array of SubmitSnapshot[], newest first.
 *
 * Cap: keeps the last 20 submissions per problem.
 *
 * CLIENT-SIDE ONLY.
 */

import type { SubmissionStorage } from '../submissionStorage.js';
import type { SubmitSnapshot } from '$lib/types/execution.js';

const MAX_SUBMISSIONS = 20;

function storageKey(problemId: string): string {
  return `submissions::${problemId}`;
}

export class LocalSubmissionStorage implements SubmissionStorage {
  async addSubmission(snapshot: SubmitSnapshot): Promise<void> {
    const existing = await this.getSubmissions(snapshot.problemId);
    const updated = [snapshot, ...existing].slice(0, MAX_SUBMISSIONS);
    try {
      localStorage.setItem(storageKey(snapshot.problemId), JSON.stringify(updated));
    } catch (err) {
      console.warn('[SubmissionStorage] Failed to save submission:', err);
    }
  }

  async getSubmissions(problemId: string): Promise<SubmitSnapshot[]> {
    try {
      const raw = localStorage.getItem(storageKey(problemId));
      if (!raw) return [];
      return JSON.parse(raw) as SubmitSnapshot[];
    } catch {
      return [];
    }
  }

  async clearSubmissions(problemId: string): Promise<void> {
    localStorage.removeItem(storageKey(problemId));
  }
}

export const localSubmissionStorage = new LocalSubmissionStorage();
