/**
 * GET /api/sessions/[id]/stream
 *
 * Server-Sent Events feed for a single session. Each chunk arrives as a
 * named SSE event:
 *
 *   event: stdout    data: {"data":"..."}
 *   event: stderr    data: {"data":"..."}
 *   event: status    data: {"status":"running"}
 *   event: exit      data: {"exitCode":0,"durationMs":1234}
 *
 * The client is expected to `new EventSource(...)` and consume events as
 * they arrive. We also emit a periodic `event: ping` so proxies don't
 * close idle connections.
 *
 * The buffered chunks attached to the live entry are replayed first so a
 * page refresh mid-run shows the full history.
 */

import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getSession, subscribeToLogs } from '$lib/server/sandbox/index.js';

const PING_INTERVAL_MS = 15_000;

function sseFrame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export const GET: RequestHandler = async ({ locals, params, request }) => {
  const rec = await getSession(locals.user!.id, params.id);
  if (!rec) throw error(404, 'Session not found');

  const encoder = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      let closed = false;
      const safeEnqueue = (s: string) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(s));
        } catch {
          closed = true;
        }
      };

      // Emit the current persisted snapshot once so the client knows the
      // baseline. After that the registry pushes chunks as they happen.
      safeEnqueue(sseFrame('snapshot', rec));

      const { unsubscribe, record } = subscribeToLogs(params.id, (chunk) => {
        if (chunk.kind === 'stdout') safeEnqueue(sseFrame('stdout', { data: chunk.data }));
        else if (chunk.kind === 'stderr') safeEnqueue(sseFrame('stderr', { data: chunk.data }));
        else if (chunk.kind === 'status') safeEnqueue(sseFrame('status', { status: chunk.status }));
        else if (chunk.kind === 'exit') {
          safeEnqueue(sseFrame('exit', { exitCode: chunk.exitCode, durationMs: chunk.durationMs }));
        }
      });

      // If the session was already terminal at the time we subscribed (no
      // live entry, just a DB row) then we'll never see a chunk. Synthesise
      // the exit frame and close immediately so EventSource doesn't reconnect.
      if (!record) {
        safeEnqueue(sseFrame('exit', {
          exitCode: rec.exitCode,
          durationMs: rec.completedAt ? rec.completedAt - rec.startedAt : 0
        }));
        try { controller.close(); } catch { /* ignore */ }
        return;
      }

      const ping = setInterval(() => {
        safeEnqueue(`: ping\n\n`);
      }, PING_INTERVAL_MS);

      const cleanup = () => {
        closed = true;
        clearInterval(ping);
        unsubscribe();
        try { controller.close(); } catch { /* ignore */ }
      };

      request.signal.addEventListener('abort', cleanup, { once: true });
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no'
    }
  });
};
