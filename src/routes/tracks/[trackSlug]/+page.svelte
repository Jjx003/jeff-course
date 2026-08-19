<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import ProgressRing from '$lib/components/ProgressRing.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let track = $derived(data.track);
  let completions = $derived(data.completions);
  let enrolled = $derived(data.enrolled);

  // Build a quick lookup: problemId → completion record.
  let completionMap = $derived.by(() => {
    const m = new Map<string, (typeof completions)[number]>();
    for (const c of completions) m.set(c.problemId, c);
    return m;
  });

  // Optional modules (appendices, deep dives) sit outside the track's spine:
  // finishing the required run should read as 100%, not as 45 of 52.
  let coreProblems = $derived(track.problems.filter((problem) => !problem.optional));
  let completedCount = $derived(
    completions.filter(
      (c) => c.completed && coreProblems.some((p) => `${track.slug}/${p.slug}` === c.problemId)
    ).length
  );
  let totalCount = $derived(coreProblems.length);
  let progress = $derived(totalCount === 0 ? 0 : completedCount / totalCount);
  let nextProblem = $derived(
    coreProblems.find((problem) => !isCompleted(problem.slug)) ?? coreProblems[0] ?? null
  );
  let totalMinutes = $derived(coreProblems.reduce((sum, problem) => sum + problem.estimatedMinutes, 0));
  let moduleCounts = $derived.by(() => {
    const counts: Record<string, number> = { coding: 0, reading: 0, quiz: 0, test: 0, drill: 0 };
    for (const problem of coreProblems) counts[problem.type] = (counts[problem.type] ?? 0) + 1;
    return counts;
  });

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };

  function isCompleted(problemSlug: string): boolean {
    return completionMap.get(`${track.slug}/${problemSlug}`)?.completed ?? false;
  }

  function moduleKind(type: string): string {
    if (type === 'reading') return 'Read';
    if (type === 'quiz') return 'Quiz';
    if (type === 'test') return 'Test';
    if (type === 'drill') return 'Drill';
    if (type === 'flashcards') return 'Cards';
    return 'Code';
  }

  function typeTone(type: string): string {
    if (type === 'reading') return 'type-reading';
    if (type === 'quiz') return 'type-quiz';
    if (type === 'test') return 'type-test';
    if (type === 'drill') return 'type-drill';
    if (type === 'flashcards') return 'type-cards';
    return 'type-code';
  }
</script>

<Header
  crumbs={[
    { label: 'Tracks', href: '/tracks' },
    { label: track.title }
  ]}
/>

<main class="flex-1 overflow-y-auto px-6 py-10 max-w-5xl mx-auto w-full">
  <section class="track-hero">
    <div class="track-header-meta">
      <div class="flex items-center gap-3 mb-2 flex-wrap">
        <h1 class="text-2xl font-bold text-slate-100">{track.title}</h1>
        <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'}">
          {track.difficulty}
        </span>
      </div>
      <p class="text-slate-400 text-sm leading-relaxed max-w-2xl">{track.description}</p>
      {#if track.tags.length > 0}
        <div class="flex gap-2 mt-3 flex-wrap">
          {#each track.tags as tag}
            <span class="badge badge-blue">{tag}</span>
          {/each}
        </div>
      {/if}
    </div>

    {#if totalCount > 0 && enrolled}
      <div class="track-hero-side">
        <ProgressRing
          value={progress}
          size={88}
          stroke={7}
          label="{Math.round(progress * 100)}%"
          sublabel="Progress"
        />
        {#if nextProblem}
          <a class="continue-link" href="/tracks/{track.slug}/problems/{nextProblem.slug}">
            {completedCount > 0 && completedCount < totalCount ? 'Continue' : completedCount === totalCount ? 'Review track' : 'Start track'}
          </a>
        {/if}
      </div>
    {:else if totalCount > 0}
      <div class="track-hero-side enroll-side">
        <span class="preview-label">Syllabus preview</span>
        <form method="POST" action="?/enroll">
          <button class="continue-link" type="submit">Enroll in course</button>
        </form>
        <span class="enroll-note">Add this course to My courses to begin.</span>
      </div>
    {/if}
  </section>

  {#if totalCount > 0 && enrolled}
    <section class="track-summary" aria-label="Track summary">
      <div>
        <span class="summary-value">{totalCount}</span>
        <span class="summary-label">Modules</span>
      </div>
      <div>
        <span class="summary-value">{Math.round(totalMinutes / 60 * 10) / 10}<span class="summary-unit">h</span></span>
        <span class="summary-label">Estimated time</span>
      </div>
      <div>
        <span class="summary-value">{moduleCounts.coding}</span>
        <span class="summary-label">Coding</span>
      </div>
      <div>
        <span class="summary-value">{moduleCounts.reading + moduleCounts.quiz + moduleCounts.test + moduleCounts.drill}</span>
        <span class="summary-label">Study and practice</span>
      </div>
    </section>
  {/if}

  <!-- Progress bar (linear) under the header for quick visual scan -->
  {#if totalCount > 0}
    <div class="progress-strip" aria-label="track completion">
      <div class="progress-strip-bar" style="width: {progress * 100}%"></div>
    </div>
    <div class="progress-strip-label">
      {completedCount}/{totalCount} completed
    </div>
  {/if}

  <!-- Problem list -->
  <div class="module-list mt-6">
    {#each track.problems as problem, idx}
      {@const done = isCompleted(problem.slug)}
      {#if problem.section && problem.section !== track.problems[idx - 1]?.section}
        <div class="section-divider">
          <span class="section-rule"></span>
          <span class="section-label">{problem.section}</span>
          <span class="section-rule"></span>
        </div>
      {/if}
      <svelte:element
        this={enrolled ? 'a' : 'div'}
        href={enrolled ? `/tracks/${track.slug}/problems/${problem.slug}` : undefined}
        class="module-row group"
        class:row-done={done}
        class:row-default={!done}
        class:row-locked={!enrolled}
      >
        <!-- Order number / check -->
        <span class="row-status">
          {#if done}
            <span class="check-mark" aria-label="completed">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 13l4 4L19 7" />
              </svg>
            </span>
          {:else}
            <span class="text-slate-600 text-sm font-mono">{String(idx + 1).padStart(2, '0')}</span>
          {/if}
        </span>

        <!-- Title + description -->
        <div class="module-copy">
          <div class="text-sm font-semibold truncate"
               class:text-slate-200={!done}
               class:text-slate-100={done}>
            {problem.title}
          </div>
          {#if problem.description}
            <div class="text-xs text-slate-500 mt-0.5 truncate">{problem.description}</div>
          {/if}
        </div>

        <!-- Metadata -->
        <div class="module-meta">
          {#if problem.optional}
            <span class="type-pill pill-optional">Optional</span>
          {/if}
          <span class="type-pill {typeTone(problem.type)}">{moduleKind(problem.type)}</span>
          <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
            {problem.difficulty}
          </span>
          <span class="text-xs text-slate-600">{problem.estimatedMinutes}m</span>
          {#if problem.type === 'coding'}
            {#each problem.languages as lang}
              <span class="text-xs text-slate-600 font-mono">{lang === 'cpp' ? 'C++' : 'Py'}</span>
            {/each}
          {/if}
        </div>

        <span class="text-slate-600 group-hover:text-slate-400 transition-colors">→</span>
      </svelte:element>
    {/each}
  </div>

  {#if track.problems.length === 0}
    <div class="rounded-xl border border-slate-700 bg-surface-900 p-8 text-center">
      <p class="text-slate-400">No problems in this track yet.</p>
      <p class="text-slate-500 text-sm mt-1">
        Add module directories with <code class="text-sky-400">module.yaml</code> inside
        <code class="text-sky-400">courses/{track.slug}/</code>.
      </p>
    </div>
  {/if}
</main>

<style>
  .track-header {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    margin-bottom: 1.25rem;
  }
  .track-hero {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid #1e293b;
  }
  .track-header-meta {
    flex: 1;
    min-width: 0;
  }
  .track-hero-side {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
  }
  .enroll-side { align-items: stretch; width: 190px; }
  .enroll-side form, .enroll-side .continue-link { width: 100%; }
  .preview-label { color: #93c5fd; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.08em; text-align: center; text-transform: uppercase; }
  .enroll-note { color: #64748b; font-size: 0.7rem; line-height: 1.45; text-align: center; }
  .continue-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 9rem;
    padding: 0.55rem 0.9rem;
    border: 1px solid rgba(96, 165, 250, 0.45);
    border-radius: 7px;
    background: #1d4ed8;
    color: #fff;
    font-size: 0.84rem;
    font-weight: 700;
    text-decoration: none;
    transition: background 140ms ease, border-color 140ms ease;
  }
  .continue-link:hover {
    background: #2563eb;
    border-color: #93c5fd;
  }
  .track-summary {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
  }
  .track-summary > div {
    min-width: 0;
    padding: 0.85rem 1rem;
    border: 1px solid #1e293b;
    border-radius: 8px;
    background: #111827;
  }
  .summary-value {
    display: block;
    color: #f8fafc;
    font-size: 1.25rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }
  .summary-unit {
    margin-left: 0.1rem;
    color: #94a3b8;
    font-size: 0.8rem;
    font-weight: 700;
  }
  .summary-label {
    display: block;
    margin-top: 0.25rem;
    color: #94a3b8;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .progress-strip {
    height: 4px;
    background: #1a1f2e;
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 0.25rem;
  }
  .progress-strip-bar {
    height: 100%;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    transition: width 600ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .progress-strip-label {
    font-size: 0.7rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }
  .module-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .module-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.15rem;
    border: 1px solid;
    border-radius: 8px;
    text-decoration: none;
    transition: border-color 150ms ease, background 150ms ease;
  }
  .row-locked { cursor: default; opacity: 0.72; }
  .row-locked:hover { border-color: #334155; background: #16181b; }
  .row-locked > span:last-child { display: none; }
  .row-locked::after { content: 'Enroll to unlock'; flex-shrink: 0; color: #64748b; font-size: 0.68rem; font-weight: 650; }
  .module-copy {
    flex: 1;
    min-width: 0;
  }
  .module-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-shrink: 0;
  }
  .type-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 3.4rem;
    padding: 0.22rem 0.5rem;
    border: 1px solid;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 750;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  /* Muted on purpose: an appendix row should read as available, not as work owed. */
  .pill-optional {
    border-color: rgba(148, 163, 184, 0.3);
    background: rgba(148, 163, 184, 0.07);
    color: #cbd5e1;
  }
  .section-divider {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    margin: 1.6rem 0 0.4rem;
  }
  .section-rule {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(148, 163, 184, 0.28), transparent);
  }
  .section-label {
    font-size: 0.7rem;
    font-weight: 750;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #94a3b8;
    white-space: nowrap;
  }
  .type-code {
    border-color: rgba(56, 189, 248, 0.3);
    background: rgba(56, 189, 248, 0.09);
    color: #7dd3fc;
  }
  .type-reading {
    border-color: rgba(52, 211, 153, 0.28);
    background: rgba(52, 211, 153, 0.08);
    color: #86efac;
  }
  .type-quiz {
    border-color: rgba(129, 140, 248, 0.32);
    background: rgba(129, 140, 248, 0.1);
    color: #a5b4fc;
  }
  .type-test {
    border-color: rgba(251, 191, 36, 0.3);
    background: rgba(251, 191, 36, 0.08);
    color: #fde68a;
  }
  .type-drill {
    border-color: rgba(244, 114, 182, 0.32);
    background: rgba(244, 114, 182, 0.08);
    color: #f9a8d4;
  }

  .type-cards {
    border-color: rgba(45, 212, 191, 0.32);
    background: rgba(45, 212, 191, 0.08);
    color: #5eead4;
  }

  /* Row variants */
  .row-default {
    border-color: #334155;
    background: #16181b;
  }
  .row-default:hover {
    border-color: #60a5fa;
    background: #1a1f2e;
  }
  .row-done {
    border-color: rgba(96, 165, 250, 0.25);
    background: linear-gradient(180deg, rgba(96, 165, 250, 0.05), #16181b);
  }
  .row-done:hover {
    border-color: rgba(96, 165, 250, 0.5);
  }

  .row-status {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    flex-shrink: 0;
  }
  .check-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 999px;
    background: rgba(96, 165, 250, 0.18);
    color: #60a5fa;
  }

  @media (max-width: 760px) {
    .track-hero {
      flex-direction: column;
    }
    .track-hero-side {
      width: 100%;
      align-items: stretch;
      flex-direction: row;
      justify-content: space-between;
    }
    .track-summary {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .module-row {
      align-items: flex-start;
    }
    .module-meta {
      align-items: flex-end;
      flex-direction: column;
      gap: 0.35rem;
    }
  }

  @media (max-width: 560px) {
    .track-hero-side {
      align-items: center;
      flex-direction: column;
    }
    .track-summary {
      grid-template-columns: 1fr;
    }
    .module-row {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 0.65rem 0.8rem;
    }
    .module-meta {
      grid-column: 2;
      align-items: flex-start;
      flex-direction: row;
      flex-wrap: wrap;
    }
  }
</style>
