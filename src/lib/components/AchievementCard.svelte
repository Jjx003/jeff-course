<script lang="ts">
  /**
   * AchievementCard
   *
   * Displays one achievement. Locked achievements show a grayed icon and a
   * progress bar; unlocked ones show the unlock date.
   */
  import type { Achievement } from '$lib/types/gamification.js';

  interface Props {
    achievement: Achievement;
  }
  let { achievement }: Props = $props();

  // Each achievement gets a small inline SVG glyph. We keep the set small
  // and consistent (line icons, currentColor).
  const ICONS: Record<string, string> = {
    'first-solve':    'M5 13l4 4L19 7',                                                              // check
    'five-solves':    'M12 2l3 7 7 .6-5.3 4.7L18 22l-6-3.5L6 22l1.3-7.7L2 9.6 9 9z',                  // star
    'twenty-solves':  'M3 12l3-9 3 9-3 9z M12 12l3-9 3 9-3 9z',                                       // double-mountain (simple)
    'streak-3':       'M12 3c2 4 5 6 5 10a5 5 0 0 1-10 0c0-4 3-6 5-10z',                              // flame
    'streak-7':       'M12 3c2 4 5 6 5 10a5 5 0 0 1-10 0c0-4 3-6 5-10z',
    'streak-30':      'M12 3c2 4 5 6 5 10a5 5 0 0 1-10 0c0-4 3-6 5-10z',
    'track-complete': 'M4 12l4 4 12-12 M4 18l4 4 12-12',                                              // double check
    'polyglot':       'M3 4h7v7H3z M14 4h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',                        // four squares
    'persistent':     'M12 2v6 M12 2l3 3 M12 2l-3 3 M4 12a8 8 0 1 0 16 0 8 8 0 1 0-16 0z',            // refresh-like
    'theorist':       'M4 6h16 M4 12h16 M4 18h10',                                                   // lines (book)
    'well-rounded':   'M12 22a10 10 0 1 0 0-20 10 10 0 1 0 0 20z M2 12h20 M12 2c3 4 3 16 0 20 M12 2c-3 4-3 16 0 20',
    // Time-based achievements: a family of clock variants that get more
    // "earned" looking as the threshold climbs.
    'hours-1':        'M12 22a10 10 0 1 0 0-20 10 10 0 1 0 0 20z M12 7v5l3 2',                       // simple clock
    'hours-10':       'M12 22a10 10 0 1 0 0-20 10 10 0 1 0 0 20z M12 7v5l3.5 2 M12 2v2 M12 20v2 M2 12h2 M20 12h2', // clock w/ tick marks
    'hours-50':       'M6 3h12 M6 21h12 M7 3c0 5 10 7 10 9 M17 3c0 5-10 7-10 9 M7 21c0-5 10-7 10-9 M17 21c0-5-10-7-10-9', // hourglass
    'hours-100':      'M9 2h6 M12 22a8 8 0 1 0 0-16 8 8 0 1 0 0 16z M12 14v-4 M19 5l2 2'              // stopwatch
  };

  const icon = $derived(ICONS[achievement.id] ?? 'M12 2v20 M2 12h20');
  const isUnlocked = $derived(achievement.unlockedAt !== null);
  const dateLabel = $derived(
    achievement.unlockedAt
      ? new Date(achievement.unlockedAt).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        })
      : ''
  );
</script>

<div class="ach-card" class:unlocked={isUnlocked}>
  <div class="ach-icon" aria-hidden="true">
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d={icon} />
    </svg>
  </div>
  <div class="ach-body">
    <div class="ach-header">
      <div class="ach-title">{achievement.title}</div>
      {#if isUnlocked}
        <div class="ach-date">Earned {dateLabel}</div>
      {/if}
    </div>
    <div class="ach-desc">{achievement.description}</div>

    {#if !isUnlocked}
      <div class="ach-progress" aria-label="progress">
        <div class="ach-progress-bar" style="width: {achievement.progress * 100}%"></div>
      </div>
      <div class="ach-progress-label">{achievement.progressLabel}</div>
    {/if}
  </div>
</div>

<style>
  .ach-card {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    padding: 1rem;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    transition: border-color 0.15s, transform 0.15s;
  }
  .ach-card.unlocked {
    border-color: rgba(96, 165, 250, 0.35);
    background: linear-gradient(180deg, rgba(96, 165, 250, 0.05), transparent);
  }
  .ach-card:hover {
    transform: translateY(-1px);
  }

  .ach-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    border-radius: 8px;
    background: #1a1f2e;
    color: #64748b;
    border: 1px solid #1e293b;
  }
  .ach-card.unlocked .ach-icon {
    background: rgba(96, 165, 250, 0.12);
    color: #60a5fa;
    border-color: rgba(96, 165, 250, 0.3);
  }

  .ach-body {
    flex: 1;
    min-width: 0;
  }
  .ach-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.2rem;
  }
  .ach-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: #cbd5e1;
  }
  .ach-card.unlocked .ach-title {
    color: #f1f5f9;
  }
  .ach-date {
    font-size: 0.66rem;
    color: #64748b;
    white-space: nowrap;
  }
  .ach-desc {
    font-size: 0.78rem;
    color: #94a3b8;
    line-height: 1.4;
  }

  .ach-progress {
    margin-top: 0.6rem;
    height: 4px;
    background: #1a1f2e;
    border-radius: 999px;
    overflow: hidden;
  }
  .ach-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    transition: width 600ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .ach-progress-label {
    margin-top: 0.3rem;
    font-size: 0.65rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }
</style>
