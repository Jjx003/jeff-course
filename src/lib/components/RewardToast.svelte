<script lang="ts">
  /**
   * RewardToast
   *
   * A small, calm notification that appears top-right when the user earns
   * points or unlocks an achievement. Designed to be informative, not
   * celebratory — fades in, holds for ~3s, fades out.
   *
   * Usage:
   *   <RewardToast bind:this={toastRef} />
   *   toastRef.show({ kind: 'points', title: '+20 pts', subtitle: 'First solve' });
   */
  let visible = $state(false);
  let kind = $state<'points' | 'achievement'>('points');
  let title = $state('');
  let subtitle = $state('');
  let hideTimer: ReturnType<typeof setTimeout> | null = null;

  interface ShowOpts {
    kind: 'points' | 'achievement';
    title: string;
    subtitle?: string;
    durationMs?: number;
  }

  export function show(opts: ShowOpts) {
    kind = opts.kind;
    title = opts.title;
    subtitle = opts.subtitle ?? '';
    visible = true;
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => { visible = false; }, opts.durationMs ?? 3200);
  }
</script>

{#if visible}
  <div
    class="reward-toast"
    class:achievement={kind === 'achievement'}
    role="status"
    aria-live="polite"
  >
    <div class="icon" aria-hidden="true">
      {#if kind === 'achievement'}
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l3 7 7 .6-5.3 4.7L18 22l-6-3.5L6 22l1.3-7.7L2 9.6 9 9z" />
        </svg>
      {:else}
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 13l4 4L19 7" />
        </svg>
      {/if}
    </div>
    <div class="body">
      <div class="title">{title}</div>
      {#if subtitle}<div class="subtitle">{subtitle}</div>{/if}
    </div>
  </div>
{/if}

<style>
  .reward-toast {
    position: fixed;
    top: 4.25rem;
    right: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.7rem 1rem;
    background: #131720;
    border: 1px solid rgba(96, 165, 250, 0.4);
    border-radius: 10px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(96, 165, 250, 0.06);
    z-index: 100;
    min-width: 220px;
    animation: toast-in 280ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .reward-toast.achievement {
    border-color: rgba(251, 191, 36, 0.45);
  }
  .icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: rgba(96, 165, 250, 0.15);
    color: #60a5fa;
    flex-shrink: 0;
  }
  .reward-toast.achievement .icon {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
  }
  .body {
    min-width: 0;
  }
  .title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1.2;
  }
  .subtitle {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.15rem;
  }

  @keyframes toast-in {
    from { opacity: 0; transform: translateY(-6px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0)    scale(1);    }
  }
</style>
