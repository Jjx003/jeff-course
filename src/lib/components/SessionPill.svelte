<script lang="ts">
  /**
   * SessionPill — small live indicator in the header.
   *
   * Shows the number of currently running/queued sandbox sessions. Pulls
   * every 2 s from /api/sessions?activeOnly=1. Hidden when the count is
   * zero so the header isn't cluttered for users who never run anything.
   */
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import type { SessionRecord } from '$lib/types/sandbox.js';

  const POLL_MS = 2_000;

  let running = $state(0);
  let queued = $state(0);
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let inflight = false;

  async function refresh() {
    if (inflight) return;
    inflight = true;
    try {
      const res = await fetch('/api/sessions?activeOnly=1');
      if (!res.ok) {
        running = 0;
        queued = 0;
        return;
      }
      const sessions = (await res.json()) as SessionRecord[];
      let r = 0;
      let q = 0;
      for (const s of sessions) {
        if (s.status === 'queued') q++;
        else if (s.status === 'starting' || s.status === 'running') r++;
      }
      running = r;
      queued = q;
    } catch {
      running = 0;
      queued = 0;
    } finally {
      inflight = false;
    }
  }

  onMount(() => {
    if (!browser) return;
    void refresh();
    pollTimer = setInterval(refresh, POLL_MS);
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
  });

  let visible = $derived(running > 0 || queued > 0);
</script>

{#if visible}
  <a href="/sessions" class="pill" title="View running and recent sessions">
    <span class="dot"></span>
    {#if running > 0}
      <span class="count">{running} running</span>
    {/if}
    {#if running > 0 && queued > 0}
      <span class="sep">·</span>
    {/if}
    {#if queued > 0}
      <span class="queued">{queued} queued</span>
    {/if}
  </a>
{/if}

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.6rem;
    background: #131b2d;
    border: 1px solid #1e3a5f;
    border-radius: 999px;
    color: #cbd5e1;
    font-size: 0.72rem;
    font-weight: 500;
    text-decoration: none;
    transition: background 0.15s, border-color 0.15s;
  }
  .pill:hover {
    background: #18233a;
    border-color: #2e588f;
  }
  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #38bdf8;
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.6);
    animation: pulse 1.6s ease-out infinite;
  }
  .sep {
    color: #475569;
  }
  .queued {
    color: #94a3b8;
  }
  @keyframes pulse {
    0%   { box-shadow: 0 0 0 0   rgba(56, 189, 248, 0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(56, 189, 248, 0);   }
    100% { box-shadow: 0 0 0 0   rgba(56, 189, 248, 0);   }
  }
</style>
