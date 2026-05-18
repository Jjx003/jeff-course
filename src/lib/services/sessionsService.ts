/**
 * SessionsService — client-side interface for the new sandboxed execution
 * pipeline.
 *
 * Unlike the legacy ExecutionService (single round-trip /api/execute), this
 * starts a session and exposes live SSE chunks through an async callback
 * shape. Callers usually want:
 *
 *   1. await start(req) — returns a session id immediately.
 *   2. subscribe(id, cb) — chunks fan in as they arrive.
 *   3. await getRecord(id) once `exit` fires — for the final verdict.
 *
 * The interface is intentionally narrow; cancellation goes through
 * cancel(id) so the server can tree-kill / docker-stop the process even
 * when the SSE connection is closed.
 */

import type {
  LogChunk,
  SandboxCapabilities,
  SessionRecord,
  StartSessionRequest,
  TrackPreference
} from '$lib/types/sandbox.js';

export interface StartSessionResponse {
  id: string;
  queued: boolean;
}

export interface SessionsService {
  start(req: StartSessionRequest): Promise<StartSessionResponse>;
  list(opts?: { activeOnly?: boolean }): Promise<SessionRecord[]>;
  get(id: string): Promise<SessionRecord | null>;
  cancel(id: string): Promise<void>;
  kill(id: string): Promise<void>;
  /**
   * Open an SSE stream for the session. Returns an unsubscribe function.
   *
   * Implementations should re-emit the buffered backlog before live chunks.
   * The `signal` lets the caller close the connection on navigation.
   */
  subscribe(id: string, cb: (chunk: LogChunk) => void, opts?: { signal?: AbortSignal }): () => void;

  capabilities(): Promise<SandboxCapabilities>;
  getPreference(trackSlug: string): Promise<TrackPreference | null>;
  setPreference(pref: TrackPreference): Promise<void>;
}
