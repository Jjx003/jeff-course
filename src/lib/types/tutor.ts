/**
 * Types for the AI tutor — a per-module chat backed by an OpenRouter model.
 *
 * Shared between the server (API routes + OpenRouter client) and the client
 * (service layer + TutorPanel component).
 */

export type TutorRole = 'user' | 'assistant';

/** A single persisted turn in a module's tutor conversation. */
export interface TutorMessage {
  id: string;
  role: TutorRole;
  content: string;
  createdAt: number;
}

/**
 * Whether the tutor is usable on this server, plus the details the UI needs
 * to explain itself. `reason` is only populated when `enabled` is false.
 */
export interface TutorConfig {
  enabled: boolean;
  model: string;
  reason?: string;
}

/**
 * What the learner sends with each turn. Everything except `message` is
 * optional page context; the module's own content (problem/theory/tips) is
 * assembled server-side so the client never has to ship it back.
 */
export interface TutorAsk {
  message: string;
  /** Current editor buffer, for coding modules. */
  code?: string;
  /** Language of `code`. */
  language?: string;
  /** Which instruction tab the learner is reading. */
  activeTab?: string;
}

/** Chunks emitted over the SSE stream while a reply is generated. */
export type TutorStreamChunk =
  | { kind: 'delta'; text: string }
  | { kind: 'done'; message: TutorMessage }
  | { kind: 'error'; message: string };
