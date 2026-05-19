<script lang="ts">
  /**
   * InlineMarkdown — renders a short markdown/LaTeX snippet without the
   * heavy prose container used by MarkdownRenderer. Optimized for use
   * inside option labels, badges, or other tight UI surfaces.
   *
   * Uses the synchronous renderMarkdown path so the HTML is available
   * during the same tick as the parent render — no loading spinner.
   */
  import { renderMarkdownSync } from '$lib/markdown/renderMarkdown.js';

  interface Props {
    content: string;
  }

  let { content }: Props = $props();

  let html = $derived(renderMarkdownSync(content));
</script>

<!-- eslint-disable-next-line svelte/no-at-html-tags -->
<span class="inline-md">{@html html}</span>

<style>
  /* Flatten the inline markdown so a single paragraph inside a button or
     chip doesn't introduce surprise vertical margins. KaTeX renders fine
     inline because rehype-katex wraps math in <span class="katex">. */
  .inline-md :global(p) {
    display: inline;
    margin: 0;
  }
  .inline-md :global(code) {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 0.85em;
    padding: 0.05em 0.3em;
    background: rgba(148, 163, 184, 0.12);
    border-radius: 3px;
  }
  .inline-md :global(strong) {
    color: inherit;
    font-weight: 600;
  }
</style>
