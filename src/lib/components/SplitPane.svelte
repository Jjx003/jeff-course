<script lang="ts">
  /**
   * SplitPane — resizable horizontal split layout.
   *
   * Accepts `left` and `right` as Svelte 5 snippets.
   * Drag the divider to resize; position is persisted in localStorage.
   */
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import type { Snippet } from 'svelte';

  interface Props {
    left: Snippet;
    right: Snippet;
  }

  let { left, right }: Props = $props();

  const STORAGE_KEY = 'split-pane-left-pct';
  const MIN_PCT = 25;
  const MAX_PCT = 75;

  let leftPct = $state(42);
  let dragging = $state(false);
  let container: HTMLDivElement;

  onMount(() => {
    if (browser) {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const val = parseFloat(saved);
        if (!isNaN(val)) leftPct = clamp(val);
      }
    }
  });

  function clamp(val: number): number {
    return Math.max(MIN_PCT, Math.min(MAX_PCT, val));
  }

  function onDividerMouseDown(e: MouseEvent) {
    e.preventDefault();
    dragging = true;
  }

  function onMouseMove(e: MouseEvent) {
    if (!dragging) return;
    const rect = container.getBoundingClientRect();
    leftPct = clamp(((e.clientX - rect.left) / rect.width) * 100);
  }

  function onMouseUp() {
    if (!dragging) return;
    dragging = false;
    if (browser) localStorage.setItem(STORAGE_KEY, String(leftPct));
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
  class="split-container"
  class:cursor-col-resize={dragging}
  bind:this={container}
  onmousemove={onMouseMove}
  onmouseup={onMouseUp}
  onmouseleave={onMouseUp}
  role="presentation"
>
  <!-- Left pane -->
  <div class="pane" style="width: {leftPct}%">
    {@render left()}
  </div>

  <!-- Drag divider -->
  <div
    class="split-divider"
    role="separator"
    aria-label="Resize panes"
    aria-orientation="vertical"
    onmousedown={onDividerMouseDown}
  >
    <div class="grip">
      <span></span><span></span><span></span><span></span>
    </div>
  </div>

  <!-- Right pane -->
  <div class="pane" style="width: {100 - leftPct}%">
    {@render right()}
  </div>
</div>

<style>
  .split-container {
    display: flex;
    height: 100%;
    width: 100%;
    overflow: hidden;
    user-select: none;
  }

  .pane {
    height: 100%;
    overflow: hidden;
    flex-shrink: 0;
  }

  .grip {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    height: 100%;
  }

  .grip span {
    display: block;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.35;
  }
</style>
