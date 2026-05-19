/**
 * QuizService interface.
 *
 * Backs the quiz module flow: read aggregate progress for the intro screen,
 * post completed attempts so the score gets persisted and (on a passing
 * attempt) the module flips to completed.
 */

import type { QuizProgress } from '$lib/types/course.js';

/** Result of recording an attempt; mirrors the server response. */
export interface AttemptOutcome {
  passed: boolean;
  bestScore: number;
  bestTotal: number;
  attempts: number;
  /** True iff this attempt was the first passing one (= first time the module flipped to complete). */
  wasNewCompletion: boolean;
}

export interface QuizService {
  getProgress(problemId: string): Promise<QuizProgress>;
  recordAttempt(problemId: string, attempt: {
    total: number;
    correct: number;
    durationMs: number;
  }): Promise<AttemptOutcome>;
}
