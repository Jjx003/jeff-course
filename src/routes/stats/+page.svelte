<script lang="ts">
  /**
   * /stats — Progress dashboard
   *
   * Calm overview of the user's progress. Hero row of high-level stats →
   * activity heatmap → side-by-side track progress and achievements →
   * personal highlights.
   *
   * All data is computed server-side; this page just renders.
   */
  import Header from '$lib/components/Header.svelte';
  import HeatmapCalendar from '$lib/components/HeatmapCalendar.svelte';
  import AchievementCard from '$lib/components/AchievementCard.svelte';
  import ProgressRing from '$lib/components/ProgressRing.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  let stats = $derived(data.stats);

  let unlockedCount = $derived(stats.achievements.filter((a) => a.unlockedAt !== null).length);
  let totalAchievements = $derived(stats.achievements.length);

  function relativeTime(epoch: number | null): string {
    if (epoch === null) return '—';
    const diff = Date.now() - epoch;
    const days = Math.floor(diff / (24 * 60 * 60 * 1000));
    if (days < 1) return 'today';
    if (days === 1) return 'yesterday';
    if (days < 30) return `${days} days ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  }

  function formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date + 'T00:00:00').toLocaleDateString(undefined, {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }

  /** Compact "Xh Ym" / "Xm" rendering for a duration in milliseconds. */
  function formatHours(ms: number): string {
    if (!ms || ms <= 0) return '0m';
    const totalMin = Math.floor(ms / 60_000);
    const h = Math.floor(totalMin / 60);
    const m = totalMin % 60;
    if (h === 0) return `${m}m`;
    return `${h}h ${m}m`;
  }

  function formatMinutesShort(ms: number): string {
    if (!ms || ms <= 0) return '0m';
    const totalMin = Math.floor(ms / 60_000);
    if (totalMin < 60) return `${totalMin}m`;
    const h = Math.floor(totalMin / 60);
    const m = totalMin % 60;
    return m === 0 ? `${h}h` : `${h}h ${m}m`;
  }

  // Hero stats are derived for nicer display.
  let heroCards = $derived<
    Array<{
      key: string;
      label: string;
      value: string | number;
      unit: string;
      hint: string;
      tone: 'warm' | 'cool' | 'muted';
    }>
  >([
    {
      key: 'streak',
      label: 'Current Streak',
      value: stats.currentStreak,
      unit: stats.currentStreak === 1 ? 'day' : 'days',
      hint: stats.practicedToday ? 'Practiced today' : 'Practice today to keep it going',
      tone: stats.practicedToday ? 'warm' : (stats.currentStreak > 0 ? 'cool' : 'muted')
    },
    {
      key: 'points',
      label: 'Total Points',
      value: stats.totalPoints,
      unit: 'pts',
      hint: `${stats.problemsSolved + stats.readingsCompleted} completions`,
      tone: stats.totalPoints > 0 ? 'cool' : 'muted'
    },
    {
      key: 'solved',
      label: 'Problems Solved',
      value: stats.problemsSolved,
      unit: stats.problemsSolved === 1 ? 'unique' : 'unique',
      hint: `${stats.totalSubmissions} submission${stats.totalSubmissions === 1 ? '' : 's'} total`,
      tone: stats.problemsSolved > 0 ? 'cool' : 'muted'
    },
    {
      key: 'time',
      label: 'Time Invested',
      value: formatHours(stats.totalActiveMs),
      unit: '',
      hint:
        stats.activeMsToday > 0
          ? `${formatMinutesShort(stats.activeMsToday)} today`
          : 'No time logged today yet',
      tone: stats.totalActiveMs > 0 ? 'cool' : 'muted'
    },
    {
      key: 'achievements',
      label: 'Achievements',
      value: unlockedCount,
      unit: `/ ${totalAchievements}`,
      hint: unlockedCount === totalAchievements ? 'All unlocked' : `${totalAchievements - unlockedCount} to go`,
      tone: unlockedCount > 0 ? 'cool' : 'muted'
    }
  ]);

  // Sort tracks: in-progress first, then untouched, then completed.
  let sortedTracks = $derived.by(() => {
    return [...stats.trackProgress].sort((a, b) => {
      const aProgress = a.total > 0 ? a.completed / a.total : 0;
      const bProgress = b.total > 0 ? b.completed / b.total : 0;
      // In-progress first
      const aActive = aProgress > 0 && aProgress < 1;
      const bActive = bProgress > 0 && bProgress < 1;
      if (aActive !== bActive) return aActive ? -1 : 1;
      // Completed last
      if (a.done !== b.done) return a.done ? 1 : -1;
      // Otherwise by progress desc
      return bProgress - aProgress;
    });
  });

  let isEmpty = $derived(
    stats.problemsSolved === 0 && stats.readingsCompleted === 0
  );
</script>

<Header crumbs={[{ label: 'Stats' }]} />

<main class="stats-main">
  <div class="stats-inner">
    <header class="page-header">
      <h1 class="page-title">Your Progress</h1>
      <p class="page-sub">Consistency over intensity. Show up, learn one thing, repeat.</p>
    </header>

    {#if isEmpty}
      <div class="empty-state">
        <div class="empty-glyph" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12h4l3-8 4 16 3-8h4" />
          </svg>
        </div>
        <h2 class="empty-title">Nothing to show yet</h2>
        <p class="empty-body">
          Solve a problem or finish a reading module and your stats will appear here.
        </p>
        <a href="/tracks" class="btn-primary">Browse Tracks →</a>
      </div>
    {/if}

    <!-- Hero row -->
    <section class="hero-row" aria-label="overview">
      {#each heroCards as card}
        <div class="hero-card tone-{card.tone}">
          <div class="hero-label">{card.label}</div>
          <div class="hero-value">
            {card.value}<span class="hero-unit">{card.unit}</span>
          </div>
          <div class="hero-hint">{card.hint}</div>
        </div>
      {/each}
    </section>

    <!-- Activity heatmap -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">Activity</h2>
        <p class="section-sub">{stats.highlights.totalActivityDays} active day{stats.highlights.totalActivityDays === 1 ? '' : 's'} in the past year</p>
      </div>
      <HeatmapCalendar days={stats.activity} />
    </section>

    <!-- Two-column: Tracks + Achievements -->
    <section class="two-col">
      <!-- Tracks -->
      <div class="col-card">
        <div class="section-header inline">
          <h2 class="section-title">Tracks</h2>
          <a href="/tracks" class="section-link">Browse all →</a>
        </div>

        {#if sortedTracks.length === 0}
          <p class="muted-line">No tracks loaded.</p>
        {:else}
          <div class="track-list">
            {#each sortedTracks as t}
              {@const pct = t.total === 0 ? 0 : t.completed / t.total}
              <a href="/tracks/{t.slug}" class="track-row" class:done={t.done}>
                <ProgressRing
                  value={pct}
                  size={52}
                  stroke={5}
                  label="{t.completed}/{t.total}"
                />
                <div class="track-meta">
                  <div class="track-title">
                    {t.title}
                    {#if t.done}<span class="done-pill">Completed</span>{/if}
                  </div>
                  <div class="track-sub">
                    {#if t.done}
                      Every module finished
                    {:else if t.completed > 0}
                      {t.total - t.completed} module{t.total - t.completed === 1 ? '' : 's'} remaining
                    {:else}
                      Not started
                    {/if}
                  </div>
                </div>
              </a>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Achievements -->
      <div class="col-card">
        <div class="section-header inline">
          <h2 class="section-title">Achievements</h2>
          <span class="section-link static">{unlockedCount} / {totalAchievements}</span>
        </div>
        <div class="achievement-list">
          {#each stats.achievements as a}
            <AchievementCard achievement={a} />
          {/each}
        </div>
      </div>
    </section>

    <!-- Highlights -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">Highlights</h2>
      </div>
      <div class="highlights-grid">
        <div class="highlight-card">
          <div class="highlight-label">Longest streak</div>
          <div class="highlight-value">{stats.highlights.longestStreak}<span class="hero-unit">day{stats.highlights.longestStreak === 1 ? '' : 's'}</span></div>
        </div>
        <div class="highlight-card">
          <div class="highlight-label">Best day</div>
          <div class="highlight-value">{stats.highlights.mostActiveDayCount}<span class="hero-unit">contribs</span></div>
          <div class="highlight-foot">{formatDate(stats.highlights.mostActiveDate)}</div>
        </div>
        <div class="highlight-card">
          <div class="highlight-label">Started</div>
          <div class="highlight-value">{relativeTime(stats.highlights.firstActivityAt)}</div>
          <div class="highlight-foot">
            {stats.highlights.firstActivityAt
              ? new Date(stats.highlights.firstActivityAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
              : 'No activity yet'}
          </div>
        </div>
        <div class="highlight-card">
          <div class="highlight-label">Readings done</div>
          <div class="highlight-value">{stats.readingsCompleted}</div>
        </div>
      </div>
    </section>
  </div>
</main>

<style>
  .stats-main {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: #0d0f10;
  }
  .stats-inner {
    max-width: 1080px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  .page-header {
    margin-bottom: 1.75rem;
  }
  .page-title {
    font-size: 1.65rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 0.35rem;
    letter-spacing: -0.01em;
  }
  .page-sub {
    color: #64748b;
    font-size: 0.9rem;
    margin: 0;
  }

  /* ── Empty state ── */
  .empty-state {
    border: 1px dashed #334155;
    border-radius: 12px;
    background: #131720;
    padding: 2.5rem 1.5rem;
    text-align: center;
    margin-bottom: 2rem;
  }
  .empty-glyph {
    width: 56px;
    height: 56px;
    margin: 0 auto 1rem;
    border-radius: 14px;
    background: #1a1f2e;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #60a5fa;
  }
  .empty-title {
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 0.5rem;
  }
  .empty-body {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0 0 1.25rem;
  }

  /* ── Hero row ── */
  .hero-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 0.85rem;
    margin-bottom: 2rem;
  }
  .hero-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    transition: border-color 0.15s, transform 0.15s;
  }
  .hero-card:hover { transform: translateY(-1px); }
  .hero-card.tone-cool { border-color: rgba(96, 165, 250, 0.18); }
  .hero-card.tone-warm {
    background: linear-gradient(180deg, rgba(251, 146, 60, 0.06), #131720);
    border-color: rgba(251, 146, 60, 0.3);
  }
  .hero-label {
    font-size: 0.7rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 600;
  }
  .hero-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-top: 0.35rem;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }
  .hero-unit {
    font-size: 0.7rem;
    color: #64748b;
    font-weight: 500;
    margin-left: 0.35rem;
    text-transform: lowercase;
    letter-spacing: 0.02em;
  }
  .hero-hint {
    margin-top: 0.6rem;
    font-size: 0.72rem;
    color: #94a3b8;
  }
  .tone-warm .hero-value { color: #fdba74; }

  /* ── Sections ── */
  .section {
    margin-bottom: 2rem;
  }
  .section-header {
    margin-bottom: 0.85rem;
  }
  .section-header.inline {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }
  .section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0;
  }
  .section-sub {
    margin: 0.2rem 0 0;
    font-size: 0.78rem;
    color: #64748b;
  }
  .section-link {
    font-size: 0.78rem;
    color: #60a5fa;
    text-decoration: none;
  }
  .section-link:hover { color: #93c5fd; }
  .section-link.static {
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }

  /* ── Two-column ── */
  .two-col {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
    gap: 1rem;
    margin-bottom: 2rem;
  }
  @media (max-width: 880px) {
    .two-col {
      grid-template-columns: 1fr;
    }
  }
  .col-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.1rem;
  }
  .col-card .section-title {
    font-size: 0.95rem;
  }

  /* ── Track list ── */
  .track-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
  .track-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.6rem 0.75rem;
    border-radius: 8px;
    border: 1px solid transparent;
    background: #16181b;
    text-decoration: none;
    transition: border-color 0.15s, background 0.15s;
  }
  .track-row:hover {
    border-color: #334155;
    background: #1a1f2e;
  }
  .track-row.done {
    background: rgba(96, 165, 250, 0.05);
    border-color: rgba(96, 165, 250, 0.2);
  }
  .track-meta {
    min-width: 0;
    flex: 1;
  }
  .track-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .track-sub {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 0.15rem;
  }
  .done-pill {
    background: rgba(96, 165, 250, 0.15);
    color: #93c5fd;
    border-radius: 999px;
    padding: 1px 7px;
    font-size: 0.6rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .muted-line {
    color: #64748b;
    font-size: 0.85rem;
  }

  /* ── Achievement list ── */
  .achievement-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }

  /* ── Highlights ── */
  .highlights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.85rem;
  }
  .highlight-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.1rem;
  }
  .highlight-label {
    font-size: 0.7rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 600;
    margin-bottom: 0.4rem;
  }
  .highlight-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }
  .highlight-foot {
    font-size: 0.7rem;
    color: #64748b;
    margin-top: 0.4rem;
  }
</style>
