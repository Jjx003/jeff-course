/**
 * Types for the AI tutor — a per-module chat backed by an OpenRouter model.
 *
 * Shared between the server (API routes + agent loop) and the client
 * (service layer + TutorPanel component).
 */

export type TutorRole = 'user' | 'assistant';

/**
 * One tool the tutor invoked while composing a reply.
 *
 * Persisted alongside the message so reopening a thread still shows what the
 * tutor looked at, not just what it concluded.
 */
export interface TutorToolStep {
  id: string;
  /** Tool name, e.g. `read_learner_code`. */
  name: string;
  /** Human phrase for the UI, e.g. "Reading your code". */
  label: string;
  /** False when the tool threw; the model is told about the failure too. */
  ok: boolean;
  durationMs: number;
}

/** A single persisted turn in a module's tutor conversation. */
export interface TutorMessage {
  id: string;
  role: TutorRole;
  content: string;
  createdAt: number;
  /** Present on assistant turns that called tools. */
  steps?: TutorToolStep[];
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
 * What the learner sends with each turn.
 *
 * Note there is no `code` field: the editor autosaves to the `drafts` table,
 * so the tutor reads the buffer server-side via the `read_learner_code` tool
 * instead of the browser re-uploading it on every message.
 */
export interface TutorAsk {
  message: string;
  /** Which language the editor has open, so tools default to the right one. */
  language?: string;
  /** Which instruction tab the learner is reading. */
  activeTab?: string;
}

/** Chunks emitted over the SSE stream while a reply is generated. */
export type TutorStreamChunk =
  | { kind: 'delta'; text: string }
  | { kind: 'tool-start'; id: string; name: string; label: string }
  | { kind: 'tool-end'; id: string; ok: boolean; durationMs: number }
  | { kind: 'done'; message: TutorMessage }
  | { kind: 'error'; message: string };
