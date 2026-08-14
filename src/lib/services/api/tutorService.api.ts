/**
 * API-backed TutorService — talks to /api/tutor/*.
 *
 * The streaming turn is a POST (it carries the message and editor buffer),
 * so we read the SSE body off the fetch response instead of using
 * EventSource.
 *
 * CLIENT-SIDE ONLY.
 */

import type { TutorService } from '../tutorService.js';
import type { TutorAsk, TutorConfig, TutorMessage, TutorStreamChunk } from '$lib/types/tutor.js';

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function threadUrl(trackSlug: string, problemSlug: string): string {
  return `/api/tutor/${encodeURIComponent(trackSlug)}/${encodeURIComponent(problemSlug)}`;
}

/**
 * Pull `event:`/`data:` pairs out of a raw SSE byte stream.
 */
async function* readSse(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<{ event: string; data: string }, void, undefined> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let split: number;
      while ((split = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, split);
        buffer = buffer.slice(split + 2);

        let event = 'message';
        const dataLines: string[] = [];
        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
        }
        if (dataLines.length > 0) yield { event, data: dataLines.join('\n') };
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
}

class ApiTutorService implements TutorService {
  async getConfig(): Promise<TutorConfig> {
    const res = await fetch('/api/tutor/config');
    return jsonOrThrow<TutorConfig>(res);
  }

  async getConversation(trackSlug: string, problemSlug: string): Promise<TutorMessage[]> {
    const res = await fetch(threadUrl(trackSlug, problemSlug));
    return jsonOrThrow<TutorMessage[]>(res);
  }

  async clearConversation(trackSlug: string, problemSlug: string): Promise<void> {
    await fetch(threadUrl(trackSlug, problemSlug), { method: 'DELETE' });
  }

  async ask(
    trackSlug: string,
    problemSlug: string,
    ask: TutorAsk,
    onChunk: (chunk: TutorStreamChunk) => void,
    opts?: { signal?: AbortSignal }
  ): Promise<void> {
    let res: Response;
    try {
      res = await fetch(`${threadUrl(trackSlug, problemSlug)}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ask),
        signal: opts?.signal
      });
    } catch (err) {
      if (opts?.signal?.aborted) return;
      onChunk({ kind: 'error', message: err instanceof Error ? err.message : String(err) });
      return;
    }

    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => res.statusText);
      onChunk({ kind: 'error', message: extractErrorMessage(text) || `Request failed (${res.status})` });
      return;
    }

    try {
      for await (const { event, data } of readSse(res.body)) {
        if (event === 'delta') {
          const parsed = JSON.parse(data) as { text: string };
          onChunk({ kind: 'delta', text: parsed.text });
        } else if (event === 'done') {
          const parsed = JSON.parse(data) as { message: TutorMessage };
          onChunk({ kind: 'done', message: parsed.message });
        } else if (event === 'error') {
          const parsed = JSON.parse(data) as { message: string };
          onChunk({ kind: 'error', message: parsed.message });
        }
      }
    } catch (err) {
      if (opts?.signal?.aborted) return;
      onChunk({ kind: 'error', message: err instanceof Error ? err.message : String(err) });
    }
  }
}

/** SvelteKit `error()` responses are JSON `{ message }`; plain text otherwise. */
function extractErrorMessage(body: string): string {
  try {
    const parsed = JSON.parse(body) as { message?: string };
    return parsed.message ?? body;
  } catch {
    return body;
  }
}

export const apiTutorService = new ApiTutorService();
