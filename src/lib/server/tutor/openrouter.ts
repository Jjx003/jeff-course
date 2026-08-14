/**
 * Minimal streaming client for the OpenRouter chat-completions API.
 *
 * SERVER-SIDE ONLY.
 *
 * OpenRouter speaks the OpenAI wire format: the response body is an SSE
 * stream of `data: {json}` lines terminated by `data: [DONE]`. We parse it
 * by hand rather than pulling in an SDK, which keeps the dependency list
 * unchanged and makes the failure modes obvious.
 *
 * One request here is a single *step*. A step ends either with assistant
 * text or with a batch of tool calls; driving the multi-step loop is
 * `agent.ts`'s job.
 */

import { readTutorSettings } from './config.js';

export interface ToolCall {
  id: string;
  name: string;
  /** Raw JSON string as emitted by the model. May be malformed. */
  arguments: string;
}

/**
 * A turn in the wire-format conversation. This is the OpenAI shape, not the
 * app's `TutorMessage`: it also carries the assistant's tool calls and the
 * `tool` result turns that answer them.
 */
export type ChatMessage =
  | { role: 'system' | 'user'; content: string }
  | { role: 'assistant'; content: string; tool_calls?: ToolCall[] }
  | { role: 'tool'; content: string; tool_call_id: string };

/** JSON Schema description of one callable tool. */
export interface ToolSpec {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

/**
 * Convert our flat `ToolCall` into the nested shape the API requires.
 *
 * This matters more than it looks: if an assistant turn's `tool_calls` are not
 * in this exact shape, the model cannot correlate the following `tool` results
 * with what it asked for, and it will simply request the same tools again.
 */
function wireMessages(messages: ChatMessage[]) {
  return messages.map((message) => {
    if (message.role !== 'assistant' || !message.tool_calls?.length) return message;
    return {
      role: 'assistant',
      // Providers expect null, not '', when a turn is only tool calls.
      content: message.content || null,
      tool_calls: message.tool_calls.map((call) => ({
        id: call.id,
        type: 'function',
        function: { name: call.name, arguments: call.arguments }
      }))
    };
  });
}

/** Emitted while a single step streams in. */
export type StepEvent =
  | { kind: 'text'; text: string }
  | { kind: 'tool-calls'; calls: ToolCall[] };

/**
 * How long the upstream stream may go silent before we give up on it.
 *
 * Generous, because a slow model on a long answer is normal; this is only
 * meant to catch a connection that has actually died. Without it a stalled
 * provider leaves the learner watching the thinking dots indefinitely.
 */
const IDLE_TIMEOUT_MS = 60_000;

/** `reader.read()`, but rejecting if no bytes arrive for IDLE_TIMEOUT_MS. */
async function readWithTimeout(
  reader: ReadableStreamDefaultReader<Uint8Array>
): Promise<ReadableStreamReadResult<Uint8Array>> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const idle = new Promise<never>((_, reject) => {
    timer = setTimeout(
      () =>
        reject(
          new Error(
            `The model stopped responding (no data for ${IDLE_TIMEOUT_MS / 1000}s). Try again.`
          )
        ),
      IDLE_TIMEOUT_MS
    );
  });
  try {
    return await Promise.race([reader.read(), idle]);
  } finally {
    clearTimeout(timer);
  }
}

interface DeltaToolCall {
  index?: number;
  id?: string;
  function?: { name?: string; arguments?: string };
}

interface StreamDelta {
  choices?: Array<{
    delta?: { content?: string | null; tool_calls?: DeltaToolCall[] };
    finish_reason?: string | null;
  }>;
  error?: { message?: string };
}

/** Convert our tool specs into the `tools` array OpenRouter expects. */
function wireTools(tools: ToolSpec[]) {
  return tools.map((tool) => ({
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.parameters
    }
  }));
}

/**
 * Fold streamed tool-call fragments into whole calls.
 *
 * The model streams a tool call across many chunks: the first carries `id`
 * and `function.name`, later ones append slices of `function.arguments`.
 * Chunks are correlated by `index`, which is why this keeps an array rather
 * than appending blindly.
 */
class ToolCallAccumulator {
  private slots: Array<{ id: string; name: string; arguments: string }> = [];

  add(deltas: DeltaToolCall[]): void {
    for (const delta of deltas) {
      const index = delta.index ?? 0;
      const slot = (this.slots[index] ??= { id: '', name: '', arguments: '' });
      if (delta.id) slot.id = delta.id;
      if (delta.function?.name) slot.name = delta.function.name;
      if (delta.function?.arguments) slot.arguments += delta.function.arguments;
    }
  }

  get isEmpty(): boolean {
    return this.slots.length === 0;
  }

  /** Drop half-formed slots; a call without a name can't be dispatched. */
  finish(): ToolCall[] {
    return this.slots
      .filter((slot) => slot.name)
      .map((slot, i) => ({
        id: slot.id || `call_${i}`,
        name: slot.name,
        arguments: slot.arguments || '{}'
      }));
  }
}

/**
 * Run one step against the configured model and yield events as they arrive.
 *
 * Throws if the tutor is unconfigured or OpenRouter rejects the request; the
 * caller is responsible for turning that into an SSE `error` frame.
 */
export async function* streamChatCompletion(
  messages: ChatMessage[],
  opts: { signal?: AbortSignal; maxTokens?: number; tools?: ToolSpec[] } = {}
): AsyncGenerator<StepEvent, void, undefined> {
  const settings = readTutorSettings();
  if (!settings.apiKey) {
    throw new Error('OPENROUTER_API_KEY is not set on the server.');
  }

  const res = await fetch(`${settings.baseUrl}/chat/completions`, {
    method: 'POST',
    signal: opts.signal,
    headers: {
      Authorization: `Bearer ${settings.apiKey}`,
      'Content-Type': 'application/json',
      // Optional OpenRouter attribution headers.
      'HTTP-Referer': 'https://github.com/jeff-course',
      'X-Title': 'jeff-course AI tutor'
    },
    body: JSON.stringify({
      model: settings.model,
      messages: wireMessages(messages),
      stream: true,
      temperature: 0.3,
      max_tokens: opts.maxTokens ?? 1200,
      ...(opts.tools?.length ? { tools: wireTools(opts.tools), tool_choice: 'auto' } : {})
    })
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`OpenRouter request failed (${res.status}): ${truncate(detail, 500)}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const toolCalls = new ToolCallAccumulator();
  let buffer = '';
  let done = false;

  try {
    while (!done) {
      const { done: streamDone, value } = await readWithTimeout(reader);
      if (streamDone) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line, but OpenRouter also emits
      // `: OPENROUTER PROCESSING` keep-alive comments between them.
      let newlineIndex: number;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex).trim();
        buffer = buffer.slice(newlineIndex + 1);

        if (!line || line.startsWith(':')) continue;
        if (!line.startsWith('data:')) continue;

        const payload = line.slice(5).trim();
        if (payload === '[DONE]') {
          done = true;
          break;
        }

        let parsed: StreamDelta;
        try {
          parsed = JSON.parse(payload) as StreamDelta;
        } catch {
          continue;
        }
        if (parsed.error?.message) {
          throw new Error(`OpenRouter error: ${parsed.error.message}`);
        }

        const delta = parsed.choices?.[0]?.delta;
        if (delta?.tool_calls?.length) toolCalls.add(delta.tool_calls);
        if (delta?.content) yield { kind: 'text', text: delta.content };
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
  }

  // Tool calls only become actionable once the step has fully streamed.
  if (!toolCalls.isEmpty) {
    const calls = toolCalls.finish();
    if (calls.length > 0) yield { kind: 'tool-calls', calls };
  }
}

function truncate(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max)}…`;
}
