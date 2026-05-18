/**
 * ApiStudyTimeService
 *
 * Posts heartbeats to `/api/study-time/heartbeat`. Errors are swallowed so a
 * transient network blip never disrupts the page — the next heartbeat will
 * carry the same running total and self-heal.
 */

import type { StudyTimeHeartbeat, StudyTimeService } from '../studyTimeService.js';

export class ApiStudyTimeService implements StudyTimeService {
  async heartbeat(payload: StudyTimeHeartbeat): Promise<void> {
    try {
      await fetch('/api/study-time/heartbeat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch {
      // Intentional: heartbeats are best-effort.
    }
  }
}

export const apiStudyTimeService = new ApiStudyTimeService();
