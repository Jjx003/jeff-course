/**
 * StudyTimeService interface.
 *
 * The client posts a periodic heartbeat with the running active-ms counter
 * for the current study session. Reading the aggregate (total + today's
 * bucket) goes through `StatsService.getSummary()` — we deliberately do NOT
 * add a separate read endpoint here, so there's one place to expand the
 * stats payload as new gamification dimensions arrive.
 */

export interface StudyTimeHeartbeat {
  sessionId: string;
  problemId: string;
  /** Running total of active ms in this session (NOT a delta). */
  activeMs: number;
  /** Epoch ms when this session began. Fixed at session creation. */
  startedAt: number;
}

export interface StudyTimeService {
  /** Fire-and-forget heartbeat. Implementations should swallow errors. */
  heartbeat(payload: StudyTimeHeartbeat): Promise<void>;
}
