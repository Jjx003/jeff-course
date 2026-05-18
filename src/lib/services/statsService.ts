/**
 * StatsService interface.
 *
 * Aggregates derived gamification data (streak, points, achievements,
 * activity heatmap, per-track progress). The local implementation calls
 * a server-side endpoint that runs the engine in `src/lib/server/stats.ts`.
 */

import type { StatsSummary } from '$lib/types/gamification.js';

export interface StatsService {
  /** Get the full stats payload. Server is the single source of truth. */
  getSummary(): Promise<StatsSummary>;
}
