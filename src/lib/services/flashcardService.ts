/**
 * FlashcardService interface.
 *
 * Deck progress is per learner and per module. Unlike quizzes, a deck has no
 * single "attempt" — every card review is its own scored event, so the client
 * posts one review at a time and gets the rescheduled card back.
 */

import type {
  FlashcardCardState,
  FlashcardDueDeck,
  FlashcardGrade,
  FlashcardProgress
} from '$lib/types/course.js';

export interface FlashcardReviewResult {
  state: FlashcardCardState;
  progress: FlashcardProgress;
  wasNewCompletion: boolean;
}

export interface FlashcardService {
  getProgress(problemId: string): Promise<FlashcardProgress>;
  review(
    problemId: string,
    review: { cardId: string; grade: FlashcardGrade; responseMs: number }
  ): Promise<FlashcardReviewResult | null>;
  reset(problemId: string): Promise<FlashcardProgress | null>;
  /** Due counts for every deck in every enrolled track. */
  getDueDecks(): Promise<FlashcardDueDeck[]>;
}
