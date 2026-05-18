/**
 * ApiStatsService
 *
 * Fetch-based implementation backed by the `/api/stats` endpoint which
 * delegates to the server-side stats engine.
 */

import type { StatsService } from '../statsService.js';
import type { StatsSummary } from '$lib/types/gamification.js';

export class ApiStatsService implements StatsService {
  async getSummary(): Promise<StatsSummary> {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error(`Failed to load stats (${res.status})`);
    const data = (await res.json()) as { stats: StatsSummary };
    return data.stats;
  }
}

export const apiStatsService = new ApiStatsService();
