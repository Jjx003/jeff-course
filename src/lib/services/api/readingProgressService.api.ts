/**
 * ApiReadingProgressService
 *
 * Fetch-based implementation backed by `/api/reading/[trackSlug]/[problemSlug]`.
 */

import type { ReadingProgressService } from '../readingProgressService.js';

function url(problemId: string): string {
  return `/api/reading/${problemId}`;
}

export class ApiReadingProgressService implements ReadingProgressService {
  async isCompleted(problemId: string): Promise<boolean> {
    const res = await fetch(url(problemId));
    if (!res.ok) return false;
    const data = (await res.json()) as { completed: boolean };
    return data.completed;
  }

  async markComplete(problemId: string): Promise<{ wasNew: boolean }> {
    const res = await fetch(url(problemId), { method: 'POST' });
    if (!res.ok) return { wasNew: false };
    const data = (await res.json()) as { wasNew: boolean };
    return data;
  }
}

export const apiReadingProgressService = new ApiReadingProgressService();
