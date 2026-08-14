/**
 * Minimal streaming client for the OpenRouter chat-completions API.
 *
 * SERVER-SIDE ONLY.
 *
 * OpenRouter speaks the OpenAI wire format: the response body is an SSE
 * stream of `data: {json}` lines terminated by `data: [DONE]`. We parse it
 * by hand rather than pulling in an SDK, which keeps the dependency list
 * unchanged and makes the failure modes obvious.
 */

import { readTutorSettings } from './config.js';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface StreamDelta {
  choices?: Array<{
    delta?: { content?: string | null };
    finish_reason?: string | null;
  }>;
  error?: { message?: string };
}

/**
 * Ask the configured model for a reply and yield text deltas as they arrive.
 *
 * Throws if the tutor is unconfigured or OpenRouter rejects the request; the
 * caller is responsible for turning that into an SSE `error` frame.
 */
export async function* streamChatCompletion(
  messages: ChatMessage[],
  opts: { signal?: AbortSignal; maxTokens?: number } = {}
): AsyncGenerator<string, void, undefined> {
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
      messages,
      stream: true,
      temperature: 0.3,
      max_tokens: opts.maxTokens ?? 1200
    })
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`OpenRouter request failed (${res.status}): ${truncate(detail, 500)}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
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
        if (payload === '[DONE]') return;

        let parsed: StreamDelta;
        try {
          parsed = JSON.parse(payload) as StreamDelta;
        } catch {
          continue;
        }
        if (parsed.error?.message) {
          throw new Error(`OpenRouter error: ${parsed.error.message}`);
        }
        const text = parsed.choices?.[0]?.delta?.content;
        if (text) yield text;
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
}

function truncate(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max)}…`;
}
