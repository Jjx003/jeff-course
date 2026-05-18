<script lang="ts">
  /**
   * StreakBadge
   *
   * Tiny pill displayed in the header. Shows the current streak (flame icon)
   * and total points. Clicks navigate to /stats.
   *
   * Renders nothing until data has loaded to avoid a layout flash.
   */
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import type { StatsSummary } from '$lib/types/gamification.js';

  let summary = $state<StatsSummary | null>(null);

  onMount(async () => {
    if (!browser) return;
    try {
      const { statsService } = await import('$lib/services/index.js');
      summary = await statsService.getSummary();
    } catch {
      summary = null;
    }
  });
</script>

{#if summary && (summary.currentStreak > 0 || summary.totalPoints > 0)}
  <a
    href="/stats"
    class="streak-badge"
    title={summary.practicedToday
      ? `${summary.currentStreak}-day streak — practiced today`
      : `${summary.currentStreak}-day streak — practice today to keep it going`}
    class:active={summary.practicedToday}
    aria-label="View statistics"
  >
    <span class="flame" aria-hidden="true">
      <!-- inline flame, kept simple -->
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M13.5 0.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5 0.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/>
      </svg>
    </span>
    <span class="streak-count">{summary.currentStreak}</span>
    <span class="divider" aria-hidden="true">·</span>
    <span class="points">{summary.totalPoints}<span class="pt">pt</span></span>
  </a>
{/if}

<style>
  .streak-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    background: #1a1f2e;
    border: 1px solid #2d3748;
    color: #cbd5e1;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none;
    transition: border-color 0.15s, background 0.15s, transform 0.15s;
    font-variant-numeric: tabular-nums;
    line-height: 1;
  }
  .streak-badge:hover {
    border-color: #475569;
    background: #1e2535;
    transform: translateY(-1px);
  }

  /* Active = practiced today; warm tint so the badge feels "alive". */
  .streak-badge.active {
    color: #fde68a;
    border-color: rgba(251, 146, 60, 0.35);
    background: rgba(251, 146, 60, 0.08);
  }
  .streak-badge.active:hover {
    border-color: rgba(251, 146, 60, 0.5);
    background: rgba(251, 146, 60, 0.12);
  }

  .flame {
    display: inline-flex;
    color: #f59e0b;
    opacity: 0.85;
  }
  .streak-badge.active .flame {
    color: #fb923c;
    animation: gentle-glow 2.6s ease-in-out infinite;
  }

  .divider {
    color: #475569;
    font-weight: 400;
  }

  .points {
    color: #94a3b8;
    font-weight: 600;
  }
  .pt {
    color: #64748b;
    font-weight: 500;
    margin-left: 0.1rem;
    font-size: 0.72rem;
  }
  .streak-badge.active .points {
    color: #cbd5e1;
  }

  @keyframes gentle-glow {
    0%, 100% { filter: drop-shadow(0 0 0 transparent); opacity: 0.85; }
    50%      { filter: drop-shadow(0 0 4px rgba(251, 146, 60, 0.55)); opacity: 1; }
  }
</style>
