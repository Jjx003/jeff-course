/**
 * Throwaway stand-in for the OpenRouter chat-completions endpoint, used to
 * exercise the AI tutor pipeline without spending tokens or needing a key.
 *
 *   node tools/tutor-mock-openrouter.mjs 8799
 *   OPENROUTER_API_KEY=test OPENROUTER_BASE_URL=http://127.0.0.1:8799/v1 npm run dev
 */

import http from 'node:http';

const port = Number(process.argv[2] ?? 8799);

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

http
  .createServer((req, res) => {
    if (!req.url?.endsWith('/chat/completions')) {
      res.writeHead(404).end('not found');
      return;
    }
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', () => {
      console.log('[mock] request bytes:', body.length);
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache'
      });
      const words = REPLY.split(/(\s+)/);
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
    });
  })
  .listen(port, () => console.log(`[mock] listening on http://127.0.0.1:${port}`));
