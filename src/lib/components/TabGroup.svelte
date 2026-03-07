<script lang="ts">
  /**
   * TabGroup
   *
   * Tab bar + content area. Content is supplied via the `children` snippet,
   * which receives `activeId` so the parent can conditionally render panels.
   */
  import type { Snippet } from 'svelte';

  interface Tab {
    id: string;
    label: string;
  }

  interface Props {
    tabs: Tab[];
    activeId?: string;
    onchange?: (id: string) => void;
    children: Snippet<[{ activeId: string }]>;
  }

  let { tabs, activeId = $bindable(tabs[0]?.id ?? ''), onchange, children }: Props = $props();

  function select(id: string) {
    activeId = id;
    onchange?.(id);
  }
</script>

<div class="tab-group">
  <div class="tab-bar" role="tablist">
    {#each tabs as tab}
      <button
        role="tab"
        class="tab-btn"
        class:active={activeId === tab.id}
        aria-selected={activeId === tab.id}
        onclick={() => select(tab.id)}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <div class="tab-content">
    {@render children({ activeId })}
  </div>
</div>

<style>
  .tab-group {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .tab-bar {
    display: flex;
    border-bottom: 1px solid rgb(51 65 85);
    flex-shrink: 0;
    padding: 0 1rem;
    gap: 0.25rem;
  }

  .tab-content {
    flex: 1;
    overflow: hidden;
  }
</style>
