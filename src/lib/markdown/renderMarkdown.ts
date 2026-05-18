/**
 * renderMarkdown.ts
 *
 * Converts a Markdown string (with inline and block LaTeX) to an HTML string.
 *
 * Pipeline:
 *   markdown string
 *     → remark-parse        (parse Markdown AST)
 *     → remark-gfm          (GitHub Flavored Markdown: tables, task lists, strikethrough)
 *     → remark-math         (identify $...$ and $$...$$ as math nodes)
 *     → remark-rehype       (convert to HTML AST)
 *     → rehype-katex        (render math nodes with KaTeX)
 *     → rehype-stringify    (serialize to HTML string)
 *
 * The pipeline is instantiated once and reused (unified processors are stateless).
 *
 * Mermaid diagrams: ```mermaid fences pass through as <pre><code class="language-mermaid">
 * blocks. They are upgraded to SVG client-side in MarkdownRenderer.svelte after
 * insertion, which avoids pulling Playwright into the SSR pipeline.
 *
 * Extension point: swap rehype-katex for MathJax or a server-side renderer
 * without changing any call sites — just update this file.
 */

import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkRehype from 'remark-rehype';
import rehypeKatex from 'rehype-katex';
import rehypeStringify from 'rehype-stringify';

// Build the processor once — unified processors are reusable and thread-safe.
const processor = unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkMath)
  .use(remarkRehype, { allowDangerousHtml: true })
  .use(rehypeKatex, {
    // KaTeX options
    throwOnError: false,   // gracefully fall back on parse errors
    strict: false,
    trust: false
  })
  .use(rehypeStringify, { allowDangerousHtml: true });

/**
 * Render a Markdown string (optionally containing LaTeX) to an HTML string.
 *
 * Safe to call server-side and client-side.
 * Returns an empty string for empty input.
 */
export async function renderMarkdown(markdown: string): Promise<string> {
  if (!markdown.trim()) return '';
  const result = await processor.process(markdown);
  return String(result);
}

/**
 * Synchronous variant — use only when async is not available.
 * Uses processSync under the hood; KaTeX rendering is synchronous anyway.
 */
export function renderMarkdownSync(markdown: string): string {
  if (!markdown.trim()) return '';
  const result = processor.processSync(markdown);
  return String(result);
}
