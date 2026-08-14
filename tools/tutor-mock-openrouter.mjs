/**
 * Throwaway stand-in for the OpenRouter chat-completions endpoint, used to
 * exercise the AI tutor pipeline without spending tokens or needing a key.
 *
 *   node tools/tutor-mock-openrouter.mjs 8799
 *   OPENROUTER_API_KEY=test OPENROUTER_BASE_URL=http://127.0.0.1:8799/v1 npm run dev
 *
 * It also exercises the agent loop: the first step of a turn answers with
 * tool calls (streamed in fragments, the way real providers do it), and the
 * follow-up step — the one that arrives carrying `tool` results — answers
 * with prose. Pass `--no-tools` to always reply with prose instead.
 */

import http from 'node:http';

const port = Number(process.argv[2] ?? 8799);
const useTools = !process.argv.includes('--no-tools');

const REPLY = `Good question. Here is the short version:

1. Start from the **definition** the module gives you.
2. Check the shape of the thing you are computing.
3. Only then write code.

$$E = mc^2$$

\`\`\`python
def hint():
    return "try the smallest failing case first"
\`\`\`

What does your current attempt produce for the simplest input?`;

/** Stream a string as OpenAI-format content deltas, then finish. */
function streamText(res, text) {
  const words = text.split(/(\s+)/);
  let i = 0;
  const timer = setInterval(() => {
    if (i >= words.length) {
      clearInterval(timer);
      res.write('data: [DONE]\n\n');
      res.end();
      return;
    }
    const chunk = { choices: [{ delta: { content: words[i++] } }] };
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  }, 15);
}

/**
 * Stream tool calls the way a real provider does: the name arrives first,
 * then the arguments in slices. This is what the accumulator has to survive.
 */
function streamToolCalls(res, calls) {
  const frames = [];
  calls.forEach((call, index) => {
    frames.push({ index, id: call.id, function: { name: call.name, arguments: '' } });
    const args = JSON.stringify(call.args);
    for (let i = 0; i < args.length; i += 7) {
      frames.push({ index, function: { arguments: args.slice(i, i + 7) } });
    }
  });

  let i = 0;
  const timer = setInterval(() => {
    if (i >= frames.length) {
      clearInterval(timer);
      res.write(
        `data: ${JSON.stringify({ choices: [{ delta: {}, finish_reason: 'tool_calls' }] })}\n\n`
      );
      res.write('data: [DONE]\n\n');
      res.end();
      return;
    }
    const chunk = { choices: [{ delta: { tool_calls: [frames[i++]] } }] };
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  }, 10);
}

/** Pick tool calls that make sense for whatever tools were advertised. */
function planCalls(request) {
  const offered = new Set(
    (request.tools ?? []).map((tool) => tool?.function?.name).filter(Boolean)
  );
  const calls = [];
  if (offered.has('read_learner_code')) {
    calls.push({ id: 'call_code', name: 'read_learner_code', args: {} });
  }
  if (offered.has('read_module_section')) {
    calls.push({ id: 'call_theory', name: 'read_module_section', args: { section: 'theory' } });
  }
  return calls;
}

http
  .createServer((req, res) => {
    if (!req.url?.endsWith('/chat/completions')) {
      res.writeHead(404).end('not found');
      return;
    }
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', () => {
      let request = {};
      try {
        request = JSON.parse(body);
      } catch {
        /* fall through to a prose reply */
      }

      const messages = request.messages ?? [];
      const alreadyRanTools = messages.some((m) => m.role === 'tool');
      const calls = useTools && !alreadyRanTools ? planCalls(request) : [];

      console.log(
        `[mock] ${messages.length} messages, ${(request.tools ?? []).length} tools offered ->`,
        calls.length > 0 ? `tool calls: ${calls.map((c) => c.name).join(', ')}` : 'prose reply'
      );
      if (alreadyRanTools) {
        for (const m of messages.filter((m) => m.role === 'tool')) {
          console.log(`[mock]   tool result (${m.content.length} chars): ${m.content.slice(0, 80)}…`);
        }
      }

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache'
      });

      if (calls.length > 0) streamToolCalls(res, calls);
      else streamText(res, REPLY);
    });
  })
  .listen(port, () => console.log(`[mock] listening on http://127.0.0.1:${port}`));
