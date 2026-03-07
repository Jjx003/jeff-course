/**
 * LocalRunHistoryStorage
 *
 * Persists run snapshots in localStorage.
 * Key pattern: `runs::{problemId}`
 * Value: JSON array of RunSnapshot[], newest first.
 *
 * Cap: keeps the last 50 runs per problem to avoid unbounded growth.
 *
 * CLIENT-SIDE ONLY.
 */

import type { RunHistoryStorage } from '../runHistoryStorage.js';
import type { RunSnapshot } from '$lib/types/execution.js';

const MAX_RUNS = 50;

function storageKey(problemId: string): string {
  return `runs::${problemId}`;
}

export class LocalRunHistoryStorage implements RunHistoryStorage {
  async addRun(snapshot: RunSnapshot): Promise<void> {
    const existing = await this.getRuns(snapshot.problemId);
    const updated = [snapshot, ...existing].slice(0, MAX_RUNS);
    try {
      localStorage.setItem(storageKey(snapshot.problemId), JSON.stringify(updated));
    } catch (err) {
      console.warn('[RunHistoryStorage] Failed to save run:', err);
    }
  }

  async getRuns(problemId: string): Promise<RunSnapshot[]> {
    try {
      const raw = localStorage.getItem(storageKey(problemId));
      if (!raw) return [];
      return JSON.parse(raw) as RunSnapshot[];
    } catch {
      return [];
    }
  }

  async clearRuns(problemId: string): Promise<void> {
    localStorage.removeItem(storageKey(problemId));
  }
}

export const localRunHistoryStorage = new LocalRunHistoryStorage();
