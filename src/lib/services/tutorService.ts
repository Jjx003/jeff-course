/**
 * TutorService — the AI tutor conversation attached to a single module.
 *
 * Interface only; see `api/tutorService.api.ts` for the implementation.
 */

import type { TutorAsk, TutorConfig, TutorMessage, TutorStreamChunk } from '$lib/types/tutor.js';

export interface TutorService {
  /** Whether the server has an OpenRouter key configured, and which model. */
  getConfig(): Promise<TutorConfig>;

  /** The saved thread for this module, oldest first. */
  getConversation(trackSlug: string, problemSlug: string): Promise<TutorMessage[]>;

  /** Delete the saved thread for this module. */
  clearConversation(trackSlug: string, problemSlug: string): Promise<void>;

  /**
   * Send one turn and stream the reply. Resolves when the reply is complete,
   * aborted, or has failed; failures surface as an `error` chunk rather than
   * a rejection so partial replies are preserved.
   */
  ask(
    trackSlug: string,
    problemSlug: string,
    ask: TutorAsk,
    onChunk: (chunk: TutorStreamChunk) => void,
    opts?: { signal?: AbortSignal }
  ): Promise<void>;
}
