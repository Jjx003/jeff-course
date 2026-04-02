/**
 * ApiDraftStorage
 *
 * Fetch-based draft storage backed by DuckDB on the server.
 * One row is kept per (problemId, language) — each save upserts in place.
 */

import type { DraftStorage } from '../draftStorage.js';
import type { Draft } from '$lib/types/execution.js';
import type { Language } from '$lib/types/course.js';

function url(problemId: string, language: Language): string {
  return `/api/drafts/${problemId}/${language}`;
}

export class ApiDraftStorage implements DraftStorage {
  async getDraft(problemId: string, language: Language): Promise<Draft | null> {
    const res = await fetch(url(problemId, language));
    const { draft } = (await res.json()) as { draft: Draft | null };
    return draft;
  }

  async saveDraft(problemId: string, language: Language, code: string): Promise<void> {
    await fetch(url(problemId, language), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async clearDraft(_problemId: string, _language: Language): Promise<void> {
    // Not implemented — drafts are overwritten, never explicitly deleted.
  }
}

export const apiDraftStorage = new ApiDraftStorage();
