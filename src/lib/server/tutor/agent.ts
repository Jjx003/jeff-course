/**
 * The tutor's agent loop.
 *
 * SERVER-SIDE ONLY.
 *
 * One "step" is one request to the model. A step either finishes with prose
 * (we're done) or with tool calls, in which case we execute them, append the
 * results, and take another step. This is the whole of the agentic behavior;
 * it is deliberately a plain loop rather than an SDK so the control flow and
 * failure modes stay visible.
 *
 * The loop is bounded by MAX_STEPS. On the last step tools are withheld,
 * which forces the model to actually answer instead of calling forever.
 */

import type { TutorToolStep } from '$lib/types/tutor.js';
import {
  streamChatCompletion,
  type ChatMessage,
  type ToolCall,
  type ToolSpec
} from './openrouter.js';
import { findTool, type ToolContext, type ToolDefinition } from './tools.js';

/** Model turns per learner turn, including the final prose answer. */
const MAX_STEPS = 4;

export type AgentEvent =
  | { kind: 'delta'; text: string }
  | { kind: 'tool-start'; id: string; name: string; label: string }
  | { kind: 'tool-end'; id: string; ok: boolean; durationMs: number };

function toSpec(tool: ToolDefinition): ToolSpec {
  return { name: tool.name, description: tool.description, parameters: tool.parameters };
}

function parseArgs(raw: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

/**
 * Execute one tool call, converting any failure into a message the model can
 * read. A thrown tool must not kill the reply — the tutor should be able to
 * say "I couldn't read your code" and carry on.
 */
async function executeCall(
  call: ToolCall,
  ctx: ToolContext
): Promise<{ step: TutorToolStep; content: string }> {
  const startedAt = Date.now();
  const tool = findTool(call.name);
  const args = parseArgs(call.arguments);

  if (!tool) {
    return {
      step: {
        id: call.id,
        name: call.name,
        label: `Unknown tool: ${call.name}`,
        ok: false,
        durationMs: 0
      },
      content: `No tool named "${call.name}" exists.`
    };
  }

  let label = tool.name;
  try {
    label = tool.label(args, ctx);
  } catch {
    /* a bad label must not sink the call */
  }

  try {
    const content = await tool.run(args, ctx);
    return {
      step: { id: call.id, name: tool.name, label, ok: true, durationMs: Date.now() - startedAt },
      content
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      step: { id: call.id, name: tool.name, label, ok: false, durationMs: Date.now() - startedAt },
      content: `The ${tool.name} tool failed: ${message}`
    };
  }
}

export interface AgentRun {
  /** Everything the model said, concatenated across steps. */
  text: string;
  steps: TutorToolStep[];
}

/**
 * Drive the loop, yielding events as they happen.
 *
 * The caller collects the same information from the events, but the returned
 * `AgentRun` is what gets persisted, so it stays authoritative.
 */
export async function* runAgent(
  seed: ChatMessage[],
  tools: ToolDefinition[],
  ctx: ToolContext,
  opts: { signal?: AbortSignal } = {}
): AsyncGenerator<AgentEvent, AgentRun, undefined> {
  const messages = [...seed];
  const specs = tools.map(toSpec);
  const allSteps: TutorToolStep[] = [];
  /** Results keyed by name+arguments, so a repeated ask is free. */
  const seen = new Map<string, string>();
  let fullText = '';
  /**
   * Set when the model asks for something it has already been given. Nothing
   * new can come of another lookup, so the next step is run without tools.
   */
  let forceAnswer = false;

  for (let step = 0; step < MAX_STEPS; step++) {
    const isLastStep = step === MAX_STEPS - 1;
    let stepText = '';
    let pendingCalls: ToolCall[] | null = null;

    for await (const event of streamChatCompletion(messages, {
      signal: opts.signal,
      // Withholding tools guarantees prose: on the final step always, and
      // early if the model has started going in circles.
      tools: isLastStep || forceAnswer ? undefined : specs
    })) {
      if (event.kind === 'text') {
        stepText += event.text;
        fullText += event.text;
        yield { kind: 'delta', text: event.text };
      } else {
        pendingCalls = event.calls;
      }
    }

    if (!pendingCalls || pendingCalls.length === 0) {
      return { text: fullText, steps: allSteps };
    }

    messages.push({ role: 'assistant', content: stepText, tool_calls: pendingCalls });

    for (const call of pendingCalls) {
      if (opts.signal?.aborted) return { text: fullText, steps: allSteps };

      const signature = `${call.name}:${call.arguments}`;
      const cached = seen.get(signature);

      if (cached !== undefined) {
        // Don't re-run the tool and don't clutter the UI with a duplicate
        // step; just remind the model it already has this.
        forceAnswer = true;
        messages.push({
          role: 'tool',
          content: `${cached}\n\n(This is the same result you were already given. Answer the learner now.)`,
          tool_call_id: call.id
        });
        continue;
      }

      const tool = findTool(call.name);
      const label = tool ? safeLabel(tool, parseArgs(call.arguments), ctx) : call.name;
      yield { kind: 'tool-start', id: call.id, name: call.name, label };

      const { step: record, content } = await executeCall(call, ctx);
      allSteps.push(record);
      seen.set(signature, content);
      yield { kind: 'tool-end', id: record.id, ok: record.ok, durationMs: record.durationMs };

      messages.push({ role: 'tool', content, tool_call_id: call.id });
    }
  }

  return { text: fullText, steps: allSteps };
}

function safeLabel(
  tool: ToolDefinition,
  args: Record<string, unknown>,
  ctx: ToolContext
): string {
  try {
    return tool.label(args, ctx);
  } catch {
    return tool.name;
  }
}
