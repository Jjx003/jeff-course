<script lang="ts">
  /**
   * HeatmapCalendar
   *
   * GitHub-style year-long activity grid. Each column is a week, each row a
   * day-of-week (Sun..Sat). Cells are colored on a five-step intensity scale
   * that uses the accent blue palette.
   *
   * The full payload is provided pre-bucketed by the server — this component
   * is purely presentational.
   */
  import type { ActivityDay } from '$lib/types/gamification.js';

  interface Props {
    days: ActivityDay[];
  }
  let { days }: Props = $props();

  // Bucket the linear `days` array into week columns aligned to Sunday.
  // The server provides exactly 52*7 entries oldest-first; we pad the first
  // week so each column has 7 cells (Sun..Sat).
  type Cell = ActivityDay | null;

  let weeks = $derived.by<Cell[][]>(() => {
    if (days.length === 0) return [];
    const out: Cell[][] = [];
    const firstDayOfWeek = new Date(days[0].date + 'T00:00:00').getDay(); // 0=Sun
    let current: Cell[] = [];
    // Leading padding so the first column visually starts on the right weekday.
    for (let i = 0; i < firstDayOfWeek; i++) current.push(null);
    for (const day of days) {
      current.push(day);
      if (current.length === 7) {
        out.push(current);
        current = [];
      }
    }
    if (current.length > 0) {
      while (current.length < 7) current.push(null);
      out.push(current);
    }
    return out;
  });

  function intensityClass(d: Cell): string {
    if (!d || d.count === 0) return 'lvl-0';
    if (d.count === 1) return 'lvl-1';
    if (d.count === 2) return 'lvl-2';
    if (d.count <= 4) return 'lvl-3';
    return 'lvl-4';
  }

  function tooltipText(d: Cell): string {
    if (!d) return '';
    const date = new Date(d.date + 'T00:00:00').toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
    if (d.count === 0) return `${date} · no activity`;
    return `${date} · ${d.count} contribution${d.count === 1 ? '' : 's'}`;
  }

  // Compute month labels from the first cell of each column when the month
  // changes. We render a small label row above the grid.
  let monthLabels = $derived.by(() => {
    const labels: { weekIndex: number; text: string }[] = [];
    let lastMonth = -1;
    weeks.forEach((week, i) => {
      const first = week.find((c) => c !== null);
      if (!first) return;
      const m = new Date(first.date + 'T00:00:00').getMonth();
      if (m !== lastMonth) {
        labels.push({
          weekIndex: i,
          text: new Date(first.date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short' })
        });
        lastMonth = m;
      }
    });
    return labels;
  });
</script>

<div class="heatmap-wrap">
  <div class="heatmap-scroll">
    <!-- Month labels -->
    <div class="month-row" style="grid-template-columns: 14px repeat({weeks.length}, 11px);">
      <div></div>
      {#each weeks as _w, i}
        {@const label = monthLabels.find((m) => m.weekIndex === i)}
        <div class="month-label">{label?.text ?? ''}</div>
      {/each}
    </div>

    <div class="grid-row">
      <!-- Day-of-week labels -->
      <div class="day-labels">
        <div></div>
        <div>Mon</div>
        <div></div>
        <div>Wed</div>
        <div></div>
        <div>Fri</div>
        <div></div>
      </div>

      <!-- The grid itself -->
      <div class="grid">
        {#each weeks as week}
          <div class="week">
            {#each week as cell}
              <div
                class="cell {intensityClass(cell)}"
                title={tooltipText(cell)}
                aria-label={tooltipText(cell)}
              ></div>
            {/each}
          </div>
        {/each}
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <span class="legend-text">Less</span>
      <div class="cell lvl-0"></div>
      <div class="cell lvl-1"></div>
      <div class="cell lvl-2"></div>
      <div class="cell lvl-3"></div>
      <div class="cell lvl-4"></div>
      <span class="legend-text">More</span>
    </div>
  </div>
</div>

<style>
  .heatmap-wrap {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1rem 0.75rem;
  }
  .heatmap-scroll {
    overflow-x: auto;
    overflow-y: hidden;
  }
  .month-row {
    display: grid;
    gap: 3px;
    margin-bottom: 4px;
    padding-left: 22px;
  }
  .month-label {
    font-size: 0.6rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    line-height: 1;
  }
  .grid-row {
    display: flex;
    gap: 6px;
  }
  .day-labels {
    display: grid;
    grid-template-rows: repeat(7, 11px);
    gap: 3px;
    font-size: 0.6rem;
    color: #64748b;
    width: 16px;
    padding-top: 0;
  }
  .day-labels > div {
    line-height: 11px;
  }
  .grid {
    display: flex;
    gap: 3px;
  }
  .week {
    display: grid;
    grid-template-rows: repeat(7, 11px);
    gap: 3px;
  }
  .cell {
    width: 11px;
    height: 11px;
    border-radius: 2.5px;
    background: #1a1f2e;
    transition: transform 0.12s, outline-color 0.15s;
    outline: 1px solid transparent;
  }
  .cell:hover {
    outline-color: rgba(96, 165, 250, 0.6);
    transform: scale(1.15);
  }
  .lvl-0 { background: #1a1f2e; }
  .lvl-1 { background: #1e3a5f; }
  .lvl-2 { background: #2563eb80; }
  .lvl-3 { background: #3b82f6; }
  .lvl-4 { background: #60a5fa; }

  .legend {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    margin-top: 0.5rem;
    font-size: 0.6rem;
    color: #64748b;
  }
  .legend-text {
    color: #64748b;
    margin: 0 0.25rem;
  }
  .legend .cell {
    width: 9px;
    height: 9px;
  }
</style>
