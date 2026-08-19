/**
 * ApiFlashcardService
 *
 * Fetch-backed spaced-repetition state. Failures are non-fatal by design: a
 * learner mid-session should keep flipping cards even if a write fails, so the
 * review call resolves to null and the caller keeps its local queue.
 */

import type {
  FlashcardDueDeck,
  FlashcardGrade,
  FlashcardProgress
} from '$lib/types/course.js';
import type { FlashcardReviewResult, FlashcardService } from '../flashcardService.js';

function emptyProgress(problemId: string): FlashcardProgress {
  return {
    problemId,
    totalCards: 0,
    seen: 0,
    learned: 0,
    due: 0,
    fresh: 0,
    reviews: 0,
    nextDueAt: null,
    hasPassed: false,
    passedAt: null,
    states: []
  };
}

export class ApiFlashcardService implements FlashcardService {
  async getProgress(problemId: string): Promise<FlashcardProgress> {
    try {
      const res = await fetch(`/api/flashcards/${problemId}`);
      if (!res.ok) return emptyProgress(problemId);
      return (await res.json()) as FlashcardProgress;
    } catch {
      return emptyProgress(problemId);
    }
  }

  async review(
    problemId: string,
    review: { cardId: string; grade: FlashcardGrade; responseMs: number }
  ): Promise<FlashcardReviewResult | null> {
    try {
      const res = await fetch(`/api/flashcards/${problemId}/review`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(review)
      });
      if (!res.ok) return null;
      return (await res.json()) as FlashcardReviewResult;
    } catch {
      return null;
    }
  }

  async reset(problemId: string): Promise<FlashcardProgress | null> {
    try {
      const res = await fetch(`/api/flashcards/${problemId}/reset`, { method: 'POST' });
      if (!res.ok) return null;
      return (await res.json()) as FlashcardProgress;
    } catch {
      return null;
    }
  }

  async getDueDecks(): Promise<FlashcardDueDeck[]> {
    try {
      const res = await fetch('/api/flashcards/due');
      if (!res.ok) return [];
      return (await res.json()) as FlashcardDueDeck[];
    } catch {
      return [];
    }
  }
}

export const apiFlashcardService = new ApiFlashcardService();
