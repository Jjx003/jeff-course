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
  const groupId = $props.id();
  const panelId = `${groupId}-tabpanel`;

  function tabId(id: string) {
    return `${groupId}-tab-${encodeURIComponent(id)}`;
  }

  function select(id: string) {
    activeId = id;
    onchange?.(id);
  }

  function handleKeydown(event: KeyboardEvent, index: number) {
    let nextIndex: number;

    switch (event.key) {
      case 'ArrowLeft':
        nextIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'ArrowRight':
        nextIndex = (index + 1) % tabs.length;
        break;
      case 'Home':
        nextIndex = 0;
        break;
      case 'End':
        nextIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    event.preventDefault();
    const nextTab = tabs[nextIndex];
    const tabList = (event.currentTarget as HTMLButtonElement).parentElement;
    const nextButton = tabList?.children[nextIndex] as HTMLButtonElement | undefined;

    if (nextTab && nextButton) {
      select(nextTab.id);
      nextButton.focus();
    }
  }
</script>

<div class="tab-group">
  <div class="tab-bar" role="tablist">
    {#each tabs as tab, index (tab.id)}
      <button
        id={tabId(tab.id)}
        type="button"
        role="tab"
        class="tab-btn"
        class:active={activeId === tab.id}
        aria-selected={activeId === tab.id}
        aria-controls={panelId}
        tabindex={activeId === tab.id ? 0 : -1}
        onclick={() => select(tab.id)}
        onkeydown={(event) => handleKeydown(event, index)}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <div
    id={panelId}
    class="tab-content"
    role="tabpanel"
    aria-labelledby={activeId ? tabId(activeId) : undefined}
    tabindex="0"
  >
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
