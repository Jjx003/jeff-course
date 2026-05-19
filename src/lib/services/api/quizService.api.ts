/**
 * ApiQuizService
 *
 * Fetch-based implementation backed by:
 *   GET  /api/quiz/[trackSlug]/[problemSlug]          → QuizProgress
 *   POST /api/quiz/[trackSlug]/[problemSlug]/attempt  → AttemptOutcome
 */

import type { QuizProgress } from '$lib/types/course.js';
import type { AttemptOutcome, QuizService } from '../quizService.js';

const DEFAULT_THRESHOLD = 0.7;

function fallbackProgress(problemId: string): QuizProgress {
  return {
    problemId,
    attempts: 0,
    bestScore: null,
    bestTotal: null,
    hasPassed: false,
    passedAt: null,
    passThreshold: DEFAULT_THRESHOLD
  };
}

export class ApiQuizService implements QuizService {
  async getProgress(problemId: string): Promise<QuizProgress> {
    try {
      const res = await fetch(`/api/quiz/${problemId}`);
      if (!res.ok) return fallbackProgress(problemId);
      const data = (await res.json()) as QuizProgress;
      return data;
    } catch {
      return fallbackProgress(problemId);
    }
  }

  async recordAttempt(
    problemId: string,
    attempt: { total: number; correct: number; durationMs: number }
  ): Promise<AttemptOutcome> {
    const res = await fetch(`/api/quiz/${problemId}/attempt`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(attempt)
    });
    if (!res.ok) {
      // The server still treats this as a "below-threshold" attempt so the
      // caller can recover gracefully.
      return {
        passed: false,
        bestScore: attempt.correct,
        bestTotal: attempt.total,
        attempts: 1,
        wasNewCompletion: false
      };
    }
    return (await res.json()) as AttemptOutcome;
  }
}

export const apiQuizService = new ApiQuizService();
