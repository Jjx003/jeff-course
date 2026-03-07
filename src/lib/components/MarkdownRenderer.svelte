<script lang="ts">
  /**
   * MarkdownRenderer
   *
   * Renders a Markdown string (with optional LaTeX) to HTML.
   * Uses the unified/remark/rehype pipeline from renderMarkdown.ts.
   *
   * Rendering happens client-side on mount so that KaTeX fonts are available.
   * A loading state is shown while rendering to avoid flash of unstyled content.
   */
  import { onMount } from 'svelte';

  interface Props {
    content: string;
  }

  let { content }: Props = $props();

  let html = $state('');
  let loading = $state(true);

  async function render() {
    if (!content.trim()) {
      html = '<p class="text-slate-500 italic">No content.</p>';
      loading = false;
      return;
    }
    loading = true;
    try {
      const { renderMarkdown } = await import('$lib/markdown/renderMarkdown.js');
      html = await renderMarkdown(content);
    } catch (err) {
      console.error('[MarkdownRenderer] render error:', err);
      html = `<pre class="text-red-400">${content}</pre>`;
    }
    loading = false;
  }

  // Re-render whenever content changes
  $effect(() => {
    // Access content inside the effect to track it
    const _ = content;
    render();
  });
</script>

{#if loading}
  <div class="flex items-center gap-2 px-6 py-8 text-slate-500">
    <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-accent-400"></span>
    <span class="text-sm">Rendering…</span>
  </div>
{:else}
  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
  <div class="prose prose-invert prose-dark max-w-none px-6 py-5 prose-sm
              prose-headings:font-semibold prose-headings:tracking-tight
              prose-a:text-accent-400 prose-a:no-underline hover:prose-a:underline
              prose-code:before:content-none prose-code:after:content-none
              prose-pre:rounded-lg prose-pre:border prose-pre:border-slate-700">
    {@html html}
  </div>
{/if}
