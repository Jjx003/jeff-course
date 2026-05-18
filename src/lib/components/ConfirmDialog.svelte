<script lang="ts">
  /**
   * ConfirmDialog
   *
   * A small, reusable modal that asks the user to confirm or cancel an
   * action. Matches the dark palette used by the rest of the app
   * (`#131720` card, `#1e293b` border, `#60a5fa` accent).
   *
   * Behaviour:
   *   - Escape  → cancel
   *   - Enter   → confirm
   *   - Backdrop click → cancel
   *   - First focus lands on the Cancel button (safer default for
   *     destructive operations)
   *
   * Usage:
   *   <ConfirmDialog
   *     bind:open
   *     title="Reset to starter code?"
   *     body="Your current code will be replaced …"
   *     tone="danger"
   *     confirmLabel="Reset"
   *     onConfirm={() => doTheThing()}
   *   />
   */
  import { tick } from 'svelte';

  interface Props {
    open: boolean;
    title: string;
    body: string;
    confirmLabel?: string;
    cancelLabel?: string;
    tone?: 'default' | 'danger';
    onConfirm: () => void | Promise<void>;
    onCancel?: () => void;
  }

  let {
    open = $bindable(),
    title,
    body,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    tone = 'default',
    onConfirm,
    onCancel
  }: Props = $props();

  let cancelButton = $state<HTMLButtonElement | undefined>(undefined);

  $effect(() => {
    if (open) {
      // Defer focus until the dialog is in the DOM.
      void tick().then(() => cancelButton?.focus());
    }
  });

  function close() {
    open = false;
  }

  function handleCancel() {
    close();
    onCancel?.();
  }

  async function handleConfirm() {
    // Close first so the dialog can't be clicked twice; the confirm callback
    // may itself be async (e.g. service call).
    close();
    await onConfirm();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!open) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      void handleConfirm();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
  <!-- Backdrop. Click anywhere outside the card to cancel. -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cd-backdrop" onclick={handleCancel}>
    <div
      class="cd-card"
      role="dialog"
      tabindex="-1"
      aria-modal="true"
      aria-labelledby="cd-title"
      aria-describedby="cd-body"
      onclick={(e) => e.stopPropagation()}
    >
      <h2 id="cd-title" class="cd-title">{title}</h2>
      <p id="cd-body" class="cd-body">{body}</p>
      <div class="cd-actions">
        <button class="btn-ghost" bind:this={cancelButton} onclick={handleCancel}>
          {cancelLabel}
        </button>
        <button
          class={tone === 'danger' ? 'btn-danger' : 'btn-primary'}
          onclick={() => void handleConfirm()}
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .cd-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    animation: cd-fade 150ms ease-out;
  }

  .cd-card {
    width: 100%;
    max-width: 420px;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.55);
    animation: cd-rise 180ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .cd-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.5rem;
    letter-spacing: -0.005em;
  }

  .cd-body {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.5;
    margin: 0 0 1.1rem;
  }

  .cd-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
  }

  @keyframes cd-fade {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  @keyframes cd-rise {
    from { opacity: 0; transform: translateY(2px) scale(0.995); }
    to   { opacity: 1; transform: translateY(0)    scale(1);    }
  }
</style>
