/**
 * Live session registry — keeps in-memory handles for sessions that are
 * currently starting/running, plus a fan-out queue for SSE log streams.
 *
 * The DuckDB row is the persistent source of truth; this map holds the
 * pieces that don't fit in a row (process handle, abort controller,
 * subscribers).
 *
 * Lives on `globalThis` so Vite HMR doesn't orphan running processes when
 * the module is re-evaluated.
 *
 * SERVER-SIDE ONLY.
 */

import type { ChildProcess } from 'node:child_process';
import type { LogChunk, SessionRecord, SessionStatus } from './types.js';

export interface LiveEntry {
  id: string;
  record: SessionRecord;
  proc: ChildProcess | null;
  /** Used to cancel a queued/in-flight session. */
  abort: AbortController;
  /** Streamed-out chunks buffered for late subscribers (capped). */
  buffer: LogChunk[];
  subscribers: Set<(chunk: LogChunk) => void>;
  /** Fires once when the session reaches a terminal status. */
  done: Promise<void>;
  resolveDone: () => void;
  /** Container name (docker mode only). */
  containerName: string | null;
}

const MAX_BUFFER_CHUNKS = 200; // 200 chunks of ~64KB each = ~12MB worst case

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
const LIVE: Map<string, LiveEntry> =
  g.__sandboxLive ?? (g.__sandboxLive = new Map<string, LiveEntry>());

export function createEntry(record: SessionRecord): LiveEntry {
  let resolveDone!: () => void;
  const done = new Promise<void>((resolve) => {
    resolveDone = resolve;
  });
  const entry: LiveEntry = {
    id: record.id,
    record,
    proc: null,
    abort: new AbortController(),
    buffer: [],
    subscribers: new Set(),
    done,
    resolveDone,
    containerName: record.containerName
  };
  LIVE.set(record.id, entry);
  return entry;
}

export function getEntry(id: string): LiveEntry | undefined {
  return LIVE.get(id);
}

export function removeEntry(id: string): void {
  LIVE.delete(id);
}

export function liveIds(): string[] {
  return Array.from(LIVE.keys());
}

export function activeCount(): number {
  return LIVE.size;
}

export function activeCountByMode(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const entry of LIVE.values()) {
    const mode = entry.record.mode;
    out[mode] = (out[mode] ?? 0) + 1;
  }
  return out;
}

/**
 * Publish a chunk to every current subscriber AND to the bounded buffer so
 * new subscribers (e.g. a page refresh mid-run) can replay recent output.
 */
export function publish(id: string, chunk: LogChunk): void {
  const entry = LIVE.get(id);
  if (!entry) return;

  entry.buffer.push(chunk);
  if (entry.buffer.length > MAX_BUFFER_CHUNKS) {
    entry.buffer.shift();
  }
  for (const sub of entry.subscribers) {
    try {
      sub(chunk);
    } catch {
      // never let one bad subscriber take down the others
    }
  }
}

/**
 * Subscribe to a session's chunk stream. Returns an unsubscribe function.
 *
 * The subscriber is immediately called once for each buffered chunk so the
 * client sees the full history, then gets live chunks as they arrive.
 */
export function subscribe(
  id: string,
  cb: (chunk: LogChunk) => void
): () => void {
  const entry = LIVE.get(id);
  if (!entry) return () => {};
  for (const chunk of entry.buffer) {
    try {
      cb(chunk);
    } catch {
      // ignore
    }
  }
  entry.subscribers.add(cb);
  return () => entry.subscribers.delete(cb);
}

/**
 * Mark a session done in-memory. The persistence layer is updated separately
 * so the row reflects the final status. Subscribers get a final `exit` chunk
 * and the entry is removed shortly after to release memory.
 */
export function markDone(id: string, finalStatus: SessionStatus, exitCode: number | null, durationMs: number): void {
  const entry = LIVE.get(id);
  if (!entry) return;
  publish(id, { kind: 'status', status: finalStatus });
  publish(id, { kind: 'exit', exitCode, durationMs });
  entry.resolveDone();
  // Leave the entry in place briefly so any SSE consumer that connects right
  // after the exit can still see the buffered tail. A 30s grace is plenty.
  setTimeout(() => {
    LIVE.delete(id);
  }, 30_000);
}

/** Patch the in-memory record (so subsequent `getEntry().record` reads are fresh). */
export function patchRecord(id: string, patch: Partial<SessionRecord>): void {
  const entry = LIVE.get(id);
  if (!entry) return;
  entry.record = { ...entry.record, ...patch };
}
