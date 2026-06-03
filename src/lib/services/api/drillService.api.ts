/**
 * ApiDrillService
 *
 * Fetch-backed drill progress and attempt persistence.
 */

import type { DrillProgress } from '$lib/types/course.js';
import type { DrillAttemptOutcome, DrillService } from '../drillService.js';

const DEFAULT_TARGET = 0.8;

function fallbackProgress(problemId: string, targetAccuracy = DEFAULT_TARGET): DrillProgress {
  return {
    problemId,
    attempts: 0,
    bestCorrect: null,
    bestTotal: null,
    bestAccuracy: null,
    bestAvgMs: null,
    bestStreak: null,
    hasPassed: false,
    passedAt: null,
    targetAccuracy
  };
}

export class ApiDrillService implements DrillService {
  async getProgress(problemId: string, targetAccuracy = DEFAULT_TARGET): Promise<DrillProgress> {
    try {
      const res = await fetch(`/api/drill/${problemId}?targetAccuracy=${targetAccuracy}`);
      if (!res.ok) return fallbackProgress(problemId, targetAccuracy);
      return (await res.json()) as DrillProgress;
    } catch {
      return fallbackProgress(problemId, targetAccuracy);
    }
  }

  async recordAttempt(
    problemId: string,
    attempt: {
      total: number;
      correct: number;
      avgMs: number;
      bestStreak: number;
      durationMs: number;
      targetAccuracy?: number;
    }
  ): Promise<DrillAttemptOutcome> {
    const res = await fetch(`/api/drill/${problemId}/attempt`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(attempt)
    });
    if (!res.ok) {
      const accuracy = attempt.total === 0 ? 0 : attempt.correct / attempt.total;
      return {
        passed: false,
        bestCorrect: attempt.correct,
        bestTotal: attempt.total,
        bestAccuracy: accuracy,
        bestAvgMs: attempt.avgMs,
        bestStreak: attempt.bestStreak,
        attempts: 1,
        wasNewCompletion: false
      };
    }
    return (await res.json()) as DrillAttemptOutcome;
  }
}

export const apiDrillService = new ApiDrillService();
