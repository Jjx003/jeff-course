/**
 * POST /api/tutor/[trackSlug]/[problemSlug]/message
 *
 * Sends one learner turn to the configured OpenRouter model and streams the
 * reply back as Server-Sent Events:
 *
 *   event: delta   data: {"text":"..."}
 *   event: done    data: {"message":{...}}
 *   event: error   data: {"message":"..."}
 *
 * This is a POST rather than a GET because the turn carries a body (the
 * message plus the current editor buffer), so the client consumes it with
 * `fetch` + a stream reader instead of `EventSource`.
 *
 * Both the learner turn and the completed reply are persisted, so the thread
 * survives a reload. A reply that is aborted mid-stream is saved with
 * whatever text arrived, which keeps the transcript honest.
 */

import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { isEnrolled } from '$lib/server/enrollments.js';
import { buildTutorContext } from '$lib/server/tutor/context.js';
import { isTutorEnabled } from '$lib/server/tutor/config.js';
import {
  HISTORY_TURN_LIMIT,
  appendMessage,
  getConversation
} from '$lib/server/tutor/conversations.js';
import { streamChatCompletion, type ChatMessage } from '$lib/server/tutor/openrouter.js';
import type { TutorAsk } from '$lib/types/tutor.js';

const MESSAGE_CHAR_LIMIT = 8000;

function sseFrame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export const POST: RequestHandler = async ({ locals, params, request }) => {
  const userId = locals.user!.id;
  const problemId = `${params.trackSlug}/${params.problemSlug}`;

  if (!isTutorEnabled()) {
    error(503, 'The AI tutor is not configured on this server.');
  }
  if (!(await isEnrolled(userId, params.trackSlug))) {
    error(403, 'Enroll in this course to use the tutor.');
  }

  let ask: TutorAsk;
  try {
    ask = (await request.json()) as TutorAsk;
  } catch {
    error(400, 'Invalid JSON body');
  }

  const question = ask.message?.trim() ?? '';
  if (!question) error(400, 'message is required');
  if (question.length > MESSAGE_CHAR_LIMIT) error(413, 'Message is too long.');

  const context = await buildTutorContext(params.trackSlug, params.problemSlug, ask);
  if (!context) error(404, `Module "${problemId}" not found`);

  const history = await getConversation(userId, problemId, HISTORY_TURN_LIMIT);
  await appendMessage(userId, problemId, 'user', question);

  const chatMessages: ChatMessage[] = [
    { role: 'system', content: context.systemPrompt },
    ...history.map((m) => ({ role: m.role, content: m.content }) as ChatMessage),
    { role: 'user', content: question }
  ];

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let closed = false;
      const send = (frame: string) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(frame));
        } catch {
          closed = true;
        }
      };

      const abort = new AbortController();
      // The browser going away should stop the upstream generation too,
      // otherwise we keep paying for tokens nobody will read.
      request.signal.addEventListener('abort', () => abort.abort(), { once: true });

      let reply = '';
      try {
        for await (const delta of streamChatCompletion(chatMessages, { signal: abort.signal })) {
          reply += delta;
          send(sseFrame('delta', { text: delta }));
        }
        const saved = await appendMessage(userId, problemId, 'assistant', reply);
        send(sseFrame('done', { message: saved }));
      } catch (err) {
        if (reply.trim()) {
          await appendMessage(userId, problemId, 'assistant', reply).catch(() => {});
        }
        const message = err instanceof Error ? err.message : String(err);
        // An abort is the learner navigating away, not a failure worth showing.
        if (!abort.signal.aborted) send(sseFrame('error', { message }));
      } finally {
        closed = true;
        try {
          controller.close();
        } catch {
          /* ignore */
        }
      }
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
