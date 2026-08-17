/**
 * API-backed SessionsService — talks to /api/sessions/* and /api/sandbox/*.
 *
 * Live log subscription uses EventSource (SSE). The server emits named
 * events (`stdout`, `stderr`, `status`, `exit`, `snapshot`) and we map them
 * into LogChunk values for callers.
 *
 * CLIENT-SIDE ONLY.
 */

import type { SessionsService, StartSessionResponse } from '../sessionsService.js';
import type {
  LogChunk,
  SandboxCapabilities,
  SessionRecord,
  StartSessionRequest,
  TrackPreference
} from '$lib/types/sandbox.js';

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

class ApiSessionsService implements SessionsService {
  async start(req: StartSessionRequest): Promise<StartSessionResponse> {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    return jsonOrThrow<StartSessionResponse>(res);
  }

  async list(opts?: { activeOnly?: boolean }): Promise<SessionRecord[]> {
    const qs = opts?.activeOnly ? '?activeOnly=1' : '';
    const res = await fetch(`/api/sessions${qs}`);
    return jsonOrThrow<SessionRecord[]>(res);
  }

  async get(id: string): Promise<SessionRecord | null> {
    const res = await fetch(`/api/sessions/${id}`);
    if (res.status === 404) return null;
    return jsonOrThrow<SessionRecord>(res);
  }

  async cancel(id: string): Promise<void> {
    await fetch(`/api/sessions/${id}/cancel`, { method: 'POST' }).catch(() => {});
  }

  async kill(id: string): Promise<void> {
    await fetch(`/api/sessions/${id}/kill`, { method: 'POST' }).catch(() => {});
  }

  subscribe(
    id: string,
    cb: (chunk: LogChunk) => void,
    opts?: { signal?: AbortSignal }
  ): () => void {
    const es = new EventSource(`/api/sessions/${id}/stream`);
    let closed = false;
    const close = () => {
      if (closed) return;
      closed = true;
      try { es.close(); } catch { /* ignore */ }
    };

    es.addEventListener('stdout', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as { data: string };
        cb({ kind: 'stdout', data: data.data });
      } catch { /* ignore */ }
    });
    es.addEventListener('stderr', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as { data: string };
        cb({ kind: 'stderr', data: data.data });
      } catch { /* ignore */ }
    });
    es.addEventListener('status', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as { status: LogChunk extends { kind: 'status'; status: infer S } ? S : never; message?: string };
        cb({ kind: 'status', status: data.status, message: data.message });
      } catch { /* ignore */ }
    });
    es.addEventListener('exit', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as { exitCode: number | null; durationMs: number };
        cb({ kind: 'exit', exitCode: data.exitCode, durationMs: data.durationMs });
      } catch { /* ignore */ }
      // No more chunks coming — close to suppress EventSource auto-reconnect.
      close();
    });
    // EventSource auto-reconnects on errors. We disable that by closing on
    // any error event; the caller can re-subscribe explicitly if needed.
    es.addEventListener('error', () => { close(); });

    opts?.signal?.addEventListener('abort', close, { once: true });

    return close;
  }

  async capabilities(): Promise<SandboxCapabilities> {
    const res = await fetch('/api/sandbox/capabilities');
    return jsonOrThrow<SandboxCapabilities>(res);
  }

  async getPreference(trackSlug: string): Promise<TrackPreference | null> {
    const res = await fetch(`/api/sandbox/preferences/${encodeURIComponent(trackSlug)}`);
    if (res.status === 404) return null;
    return jsonOrThrow<TrackPreference>(res);
  }

  async prewarm(problemId: string): Promise<void> {
    await fetch('/api/sandbox/prewarm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problemId })
    }).catch(() => {
      // Best effort — a missed warm-up just means the next run is slower.
    });
  }

  async setPreference(pref: TrackPreference): Promise<void> {
    await fetch(`/api/sandbox/preferences/${encodeURIComponent(pref.trackSlug)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preferredMode: pref.preferredMode, resources: pref.resources })
    });
  }
}

export const apiSessionsService = new ApiSessionsService();
