/**
 * POST /api/tutor/[trackSlug]/[problemSlug]/message
 *
 * Runs one learner turn through the tutor's agent loop and streams the reply
 * back as Server-Sent Events:
 *
 *   event: delta       data: {"text":"..."}
 *   event: tool-start  data: {"id":"...","name":"...","label":"..."}
 *   event: tool-end    data: {"id":"...","ok":true,"durationMs":12}
 *   event: done        data: {"message":{...}}
 *   event: error       data: {"message":"..."}
 *
 * This is a POST rather than a GET because the turn carries a body, so the
 * client consumes it with `fetch` + a stream reader instead of `EventSource`.
 *
 * The body no longer carries the editor buffer: the tutor reads it from the
 * `drafts` table through a tool when it actually needs it.
 *
 * Both the learner turn and the completed reply are persisted, so the thread
 * survives a reload. A reply that is aborted mid-stream is saved with
 * whatever text arrived, which keeps the transcript honest.
 */

import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { isEnrolled } from '$lib/server/enrollments.js';
import { runAgent } from '$lib/server/tutor/agent.js';
import { buildTutorContext } from '$lib/server/tutor/context.js';
import { isTutorEnabled, readTutorSettings } from '$lib/server/tutor/config.js';
import { toolsFor, type ToolContext } from '$lib/server/tutor/tools.js';
import {
  HISTORY_TURN_LIMIT,
  appendMessage,
  getConversation
} from '$lib/server/tutor/conversations.js';
import type { ChatMessage } from '$lib/server/tutor/openrouter.js';
import type { TutorAsk, TutorToolStep } from '$lib/types/tutor.js';

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

  const seed: ChatMessage[] = [
    { role: 'system', content: context.systemPrompt },
    ...history.map((m) => ({ role: m.role, content: m.content }) as ChatMessage),
    { role: 'user', content: question }
  ];

  const toolContext: ToolContext = {
    userId,
    problemId,
    track: context.track,
    problem: context.problem,
    allowSolutions: readTutorSettings().allowSolutions,
    language: ask.language
  };
  const tools = toolsFor(context.problem);

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
      // Built up as events arrive so an aborted turn still persists the tool
      // activity that had already happened, with real names and labels.
      const steps: TutorToolStep[] = [];
      try {
        const run = runAgent(seed, tools, toolContext, { signal: abort.signal });
        for (;;) {
          const next = await run.next();
          if (next.done) {
            reply = next.value.text;
            break;
          }
          const event = next.value;
          if (event.kind === 'delta') {
            reply += event.text;
            send(sseFrame('delta', { text: event.text }));
          } else if (event.kind === 'tool-start') {
            steps.push({
              id: event.id,
              name: event.name,
              label: event.label,
              ok: false,
              durationMs: 0
            });
            send(sseFrame('tool-start', { id: event.id, name: event.name, label: event.label }));
          } else {
            const pending = steps.find((s) => s.id === event.id);
            if (pending) {
              pending.ok = event.ok;
              pending.durationMs = event.durationMs;
            }
            send(sseFrame('tool-end', { id: event.id, ok: event.ok, durationMs: event.durationMs }));
          }
        }

        // A turn that produced only tool calls and no prose is a failure, not
        // a reply. Persisting it would leave a blank assistant bubble in the
        // thread forever, so surface it as an error the learner can retry.
        if (!reply.trim()) {
          send(
            sseFrame('error', {
              message:
                'The tutor looked things up but never wrote an answer. Try asking again, or rephrase the question.'
            })
          );
          return;
        }

        const saved = await appendMessage(userId, problemId, 'assistant', reply, steps);
        send(sseFrame('done', { message: saved }));
      } catch (err) {
        if (reply.trim()) {
          await appendMessage(userId, problemId, 'assistant', reply, steps).catch(() => {});
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
