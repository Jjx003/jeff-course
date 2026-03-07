/**
 * DraftStorage interface.
 *
 * Persists the user's current working code for each (problemId, language) pair.
 * Updated on every keystroke (debounced by the editor component).
 *
 * Local implementation: localStorage.
 * Future remote implementation: PATCH /api/drafts/:problemId
 */

import type { Draft } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

export interface DraftStorage {
  /** Load the saved draft, or null if none exists. */
  getDraft(problemId: string, language: Language): Promise<Draft | null>;

  /** Save (overwrite) the current draft. */
  saveDraft(problemId: string, language: Language, code: string): Promise<void>;

  /** Remove the draft (e.g. after a successful submit). Optional. */
  clearDraft(problemId: string, language: Language): Promise<void>;
}
