/**
 * LocalDraftStorage
 *
 * Persists drafts in localStorage as JSON.
 * Key pattern: `draft::{problemId}::{language}`
 *
 * CLIENT-SIDE ONLY. Guard all calls with `browser` checks or call only from
 * onMount / event handlers.
 */

import type { DraftStorage } from '../draftStorage.js';
import type { Draft } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

function storageKey(problemId: string, language: Language): string {
  return `draft::${problemId}::${language}`;
}

export class LocalDraftStorage implements DraftStorage {
  async getDraft(problemId: string, language: Language): Promise<Draft | null> {
    try {
      const raw = localStorage.getItem(storageKey(problemId, language));
      if (!raw) return null;
      return JSON.parse(raw) as Draft;
    } catch {
      return null;
    }
  }

  async saveDraft(problemId: string, language: Language, code: string): Promise<void> {
    const draft: Draft = { problemId, language, code, lastSavedAt: Date.now() };
    try {
      localStorage.setItem(storageKey(problemId, language), JSON.stringify(draft));
    } catch (err) {
      console.warn('[DraftStorage] Failed to save draft:', err);
    }
  }

  async clearDraft(problemId: string, language: Language): Promise<void> {
    localStorage.removeItem(storageKey(problemId, language));
  }
}

export const localDraftStorage = new LocalDraftStorage();
