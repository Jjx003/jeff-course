<script lang="ts">
  /**
   * MarkdownRenderer
   *
   * Renders a Markdown string (with optional LaTeX and Mermaid diagrams) to HTML.
   * Uses the unified/remark/rehype pipeline from renderMarkdown.ts.
   *
   * Mermaid diagrams (```mermaid fences) are upgraded from <pre><code> blocks
   * to inline SVG after the HTML is inserted into the DOM. This avoids the
   * heavy server-side rendering requirements of rehype-mermaid (Playwright).
   * If the `mermaid` package is not installed, blocks render as plain code
   * with a small notice — the rest of the markdown still works.
   *
   * Rendering happens client-side on mount so that KaTeX fonts are available.
   */
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  interface Props {
    content: string;
    variant?: 'default' | 'reading' | 'study' | 'compact';
    headingPrefix?: string;
  }

  let { content, variant = 'default', headingPrefix = 'md' }: Props = $props();

  let html = $state('');
  let loading = $state(true);
  let container = $state<HTMLDivElement>();
  let expandedImage = $state<{ src: string; alt: string } | null>(null);

  function slugify(text: string): string {
    const slug = text
      .toLowerCase()
      .replace(/<[^>]+>/g, '')
      .replace(/[`*_~[\]()]/g, '')
      .replace(/&[a-z0-9#]+;/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return slug || 'section';
  }

  function assignHeadingIds(root: HTMLElement | null | undefined) {
    if (!root) return;
    const seen = new Map<string, number>();
    const headings = root.querySelectorAll<HTMLHeadingElement>('h1, h2, h3, h4');

    for (const heading of headings) {
      const base = `${headingPrefix}-${slugify(heading.textContent ?? '')}`;
      const count = seen.get(base) ?? 0;
      seen.set(base, count + 1);
      const id = count === 0 ? base : `${base}-${count + 1}`;
      heading.id = id;
      heading.dataset.markdownHeadingId = id;
    }
  }

  /**
   * Find every <pre><code class="language-mermaid">…</code></pre> in the
   * container and replace it with the SVG produced by mermaid.render().
   * Each diagram gets a unique id so concurrent renders don't collide.
   */
  async function upgradeMermaidBlocks(root: HTMLElement | null | undefined) {
    if (!root || !browser) return;

    const blocks = root.querySelectorAll<HTMLElement>('pre > code.language-mermaid');
    if (blocks.length === 0) return;

    let mermaid: typeof import('mermaid').default;
    try {
      mermaid = (await import('mermaid')).default;
    } catch (err) {
      console.warn('[MarkdownRenderer] mermaid not available; leaving fences as code blocks', err);
      return;
    }

    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        background: '#0f1117',
        primaryColor: '#1e293b',
        primaryTextColor: '#e2e8f0',
        primaryBorderColor: '#475569',
        lineColor: '#64748b',
        secondaryColor: '#1e2535',
        tertiaryColor: '#131720',
        fontSize: '14px'
      },
      securityLevel: 'strict',
      fontFamily: 'Inter, system-ui, sans-serif'
    });

    let counter = 0;
    for (const codeEl of blocks) {
      const pre = codeEl.parentElement;
      if (!pre) continue;
      const source = codeEl.textContent ?? '';
      const id = `mermaid-${Date.now()}-${counter++}`;
      try {
        const { svg } = await mermaid.render(id, source);
        const wrapper = document.createElement('div');
        wrapper.className = 'mermaid-diagram';
        wrapper.innerHTML = svg;
        pre.replaceWith(wrapper);
      } catch (err) {
        console.warn('[MarkdownRenderer] mermaid render error', err);
        pre.classList.add('mermaid-error');
      }
    }
  }

  function enhanceImages(root: HTMLElement | null | undefined) {
    if (!root || !browser) return;

    const images = root.querySelectorAll<HTMLImageElement>('img');
    for (const image of images) {
      image.dataset.expandableImage = 'true';
      image.tabIndex = 0;
      image.setAttribute('role', 'button');
      image.setAttribute('title', 'Open image');
      image.setAttribute('aria-label', image.alt ? `Open image: ${image.alt}` : 'Open image');
    }
  }

  function openImage(image: HTMLImageElement) {
    expandedImage = {
      src: image.currentSrc || image.src,
      alt: image.alt || 'Course image'
    };
  }

  function closeImage() {
    expandedImage = null;
  }

  function handleMarkdownClick(event: MouseEvent) {
    const target = event.target;
    if (!(target instanceof HTMLImageElement)) return;
    openImage(target);
  }

  function handleMarkdownKeydown(event: KeyboardEvent) {
    const target = event.target;
    if (!(target instanceof HTMLImageElement)) return;
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    openImage(target);
  }

  function handleWindowKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && expandedImage) closeImage();
  }

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
    // After Svelte flushes the new HTML into the container, upgrade mermaid blocks.
    queueMicrotask(() => {
      assignHeadingIds(container);
      upgradeMermaidBlocks(container);
      enhanceImages(container);
    });
  }

  $effect(() => {
    const _ = content;
    const __ = headingPrefix;
    render();
  });

  $effect(() => {
    const root = container;
    if (!root) return;

    const clickListener = (event: MouseEvent) => handleMarkdownClick(event);
    const keydownListener = (event: KeyboardEvent) => handleMarkdownKeydown(event);
    root.addEventListener('click', clickListener);
    root.addEventListener('keydown', keydownListener);

    return () => {
      root.removeEventListener('click', clickListener);
      root.removeEventListener('keydown', keydownListener);
    };
  });

  onMount(() => {
    assignHeadingIds(container);
    upgradeMermaidBlocks(container);
    enhanceImages(container);
  });
</script>

<svelte:window onkeydown={handleWindowKeydown} />

{#if loading}
  <div class="flex items-center gap-2 px-6 py-8 text-slate-500">
    <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-accent-400"></span>
    <span class="text-sm">Rendering…</span>
  </div>
{:else}
  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
  <div
    bind:this={container}
    class="prose prose-invert prose-dark max-w-none
              {variant === 'reading' ? 'markdown-reading prose-base px-0 py-5' : ''}
              {variant === 'study' ? 'markdown-study prose-sm px-6 py-5' : ''}
              {variant === 'compact' ? 'markdown-compact prose-sm px-0 py-0' : ''}
              {variant === 'default' ? 'prose-sm px-6 py-5' : ''}
              prose-headings:font-semibold prose-headings:tracking-tight
              prose-a:text-accent-400 prose-a:no-underline hover:prose-a:underline
              prose-code:before:content-none prose-code:after:content-none
              prose-pre:rounded-lg prose-pre:border prose-pre:border-slate-700">
    {@html html}
  </div>
{/if}

{#if expandedImage}
  <div class="image-modal-shell">
    <button class="image-modal-backdrop" type="button" aria-label="Close image" onclick={closeImage}></button>
    <div
      class="image-modal"
      role="dialog"
      tabindex="-1"
      aria-modal="true"
      aria-label={expandedImage.alt}>
      <div class="image-modal-toolbar">
        <div class="image-modal-title">{expandedImage.alt}</div>
        <button type="button" class="image-modal-close" aria-label="Close image" onclick={closeImage}>
          x
        </button>
      </div>
      <div class="image-modal-canvas">
        <img src={expandedImage.src} alt={expandedImage.alt} />
      </div>
    </div>
  </div>
{/if}

<style>
  :global(.mermaid-diagram) {
    display: flex;
    justify-content: center;
    margin: 1.5rem 0;
    padding: 1rem;
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 8px;
    overflow-x: auto;
  }
  :global(.mermaid-diagram svg) {
    max-width: 100%;
    height: auto;
  }
  :global(.mermaid-error) {
    border-color: #b91c1c !important;
  }
  :global(.prose :where(h1, h2, h3, h4)[data-markdown-heading-id]) {
    scroll-margin-top: 1.25rem;
  }
  :global(.prose img[data-expandable-image='true']) {
    cursor: zoom-in;
    transition:
      border-color 150ms ease,
      box-shadow 150ms ease;
  }
  :global(.prose img[data-expandable-image='true']:hover),
  :global(.prose img[data-expandable-image='true']:focus-visible) {
    border-color: rgb(56 189 248 / 0.75);
    box-shadow: 0 0 0 3px rgb(56 189 248 / 0.16);
    outline: none;
  }
  .image-modal-shell {
    position: fixed;
    inset: 0;
    z-index: 80;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .image-modal-backdrop {
    position: absolute;
    inset: 0;
    display: block;
    height: 100%;
    width: 100%;
    cursor: zoom-out;
    border: 0;
    background: rgb(2 6 23 / 0.86);
    backdrop-filter: blur(10px);
  }
  .image-modal {
    position: relative;
    z-index: 1;
    display: flex;
    max-height: min(94vh, 1100px);
    width: min(92vw, 1200px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid rgb(71 85 105 / 0.9);
    border-radius: 10px;
    background: #020617;
    box-shadow: 0 24px 80px rgb(0 0 0 / 0.55);
  }
  .image-modal-toolbar {
    display: flex;
    min-height: 3rem;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border-bottom: 1px solid rgb(30 41 59 / 0.95);
    padding: 0.5rem 0.75rem 0.5rem 1rem;
  }
  .image-modal-title {
    overflow: hidden;
    color: #cbd5e1;
    font-size: 0.875rem;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .image-modal-close {
    display: inline-flex;
    height: 2rem;
    width: 2rem;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 1.25rem;
    line-height: 1;
  }
  .image-modal-close:hover,
  .image-modal-close:focus-visible {
    background: rgb(51 65 85 / 0.8);
    color: #f8fafc;
    outline: none;
  }
  .image-modal-canvas {
    overflow: auto;
    padding: 1rem;
  }
  .image-modal-canvas img {
    display: block;
    width: auto;
    max-width: 100%;
    max-height: calc(94vh - 6rem);
    height: auto;
    margin: 0 auto;
    border-radius: 6px;
    background: #f8fafc;
  }
</style>
