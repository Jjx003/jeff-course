/**
 * ApiRunHistoryStorage
 *
 * Fetch-based run storage backed by DuckDB on the server.
 * Only ONE run is kept per (problemId, language) — each new run overwrites
 * the previous one. getRuns returns at most one row per language.
 */

import type { RunHistoryStorage } from '../runHistoryStorage.js';
import type { RunSnapshot } from '$lib/types/execution.js';

export class ApiRunHistoryStorage implements RunHistoryStorage {
  async addRun(snapshot: RunSnapshot): Promise<void> {
    await fetch(`/api/runs/${snapshot.problemId}/${snapshot.language}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(snapshot)
    });
  }

  async getRuns(problemId: string): Promise<RunSnapshot[]> {
    const res = await fetch(`/api/runs/${problemId}`);
    const { runs } = (await res.json()) as { runs: RunSnapshot[] };
    return runs;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async clearRuns(_problemId: string): Promise<void> {
    // Not implemented.
  }
}

export const apiRunHistoryStorage = new ApiRunHistoryStorage();
