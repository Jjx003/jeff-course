/**
 * DrillService interface.
 *
 * Replayable drills record speed, accuracy, and streak metrics so the UI can
 * show personal improvement over time without overloading quiz attempts.
 */

import type { DrillProgress } from '$lib/types/course.js';

export interface DrillAttemptOutcome {
  passed: boolean;
  bestCorrect: number;
  bestTotal: number;
  bestAccuracy: number;
  bestAvgMs: number | null;
  bestStreak: number;
  attempts: number;
  wasNewCompletion: boolean;
}

export interface DrillService {
  getProgress(problemId: string, targetAccuracy?: number): Promise<DrillProgress>;
  recordAttempt(problemId: string, attempt: {
    total: number;
    correct: number;
    avgMs: number;
    bestStreak: number;
    durationMs: number;
    targetAccuracy?: number;
  }): Promise<DrillAttemptOutcome>;
}
