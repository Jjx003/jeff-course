<script lang="ts">
  /**
   * ReadingView - textbook-style full-width layout for `type: reading` modules.
   *
   * The default page mode renders the whole module as one scrollable article.
   * Focus mode uses the same markdown source, split into smaller steps for a
   * gradual reader experience.
   */
  import { onMount, tick } from 'svelte';
  import { browser } from '$app/environment';
  import Header from '$lib/components/Header.svelte';
  import CourseExplorer, { type ExplorerSection } from '$lib/components/CourseExplorer.svelte';
  import GradualReadingView from '$lib/components/GradualReadingView.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import { buildGradualReadSteps } from '$lib/reading/gradualReader.js';
  import type { Problem, ProblemMeta, Track } from '$lib/types/course.js';

  interface Props {
    track: Track;
    problem: Problem;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
    initiallyCompleted?: boolean;
    onMarkedComplete?: () => void;
  }

  let {
    track,
    problem,
    prevProblem,
    nextProblem,
    initiallyCompleted = false,
    onMarkedComplete
  }: Props = $props();

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner: 'badge-green',
    intermediate: 'badge-yellow',
    advanced: 'badge-red'
  };
  let hasTheory = $derived(problem.tabs.theory.trim().length > 0);
  let hasFurther = $derived(problem.tabs.tips.trim().length > 0);
  let readingMain = $state<HTMLElement | undefined>(undefined);
  let explorerOpen = $state(true);
  let activeExplorerSection = $state('problem');
  let activeExplorerHeadingId = $state('');
  let readingMode = $state<'page' | 'focus'>('page');
  let activeFocusIndex = $state(0);
  let programmaticScrollUntil = 0;
  let lastKnownScrollTop = 0;

  let explorerSections = $derived.by<ExplorerSection[]>(() => [
    { id: 'problem', label: 'Overview', content: problem.tabs.problem },
    ...(hasTheory ? [{ id: 'theory', label: 'Deep dive', content: problem.tabs.theory }] : []),
    ...(hasFurther ? [{ id: 'tips', label: 'Further reading', content: problem.tabs.tips }] : [])
  ]);
  let gradualSteps = $derived(buildGradualReadSteps(explorerSections));
  let focusActiveSection = $derived(gradualSteps[activeFocusIndex]?.sectionId ?? 'problem');
  let focusActiveHeadingId = $derived(gradualSteps[activeFocusIndex]?.headingIds[0] ?? '');

  function selectReadingMode(mode: 'page' | 'focus') {
    readingMode = mode;
    if (browser) localStorage.setItem('reading-mode', mode);
  }

  function setActiveFocusIndex(index: number) {
    activeFocusIndex = index;
    scrollReadingMainTo(0);
  }

  function focusIndexForSection(sectionId: string): number {
    const index = gradualSteps.findIndex((step) => step.sectionId === sectionId);
    return index === -1 ? 0 : index;
  }

  function focusIndexForHeading(sectionId: string, headingId: string): number {
    const exact = gradualSteps.findIndex((step) => step.headingIds.includes(headingId));
    if (exact !== -1) return exact;
    return focusIndexForSection(sectionId);
  }

  async function scrollToExplorerTarget(sectionId: string, headingId?: string) {
    activeExplorerSection = sectionId;
    activeExplorerHeadingId = headingId ?? '';
    await tick();
    const selector = headingId
      ? `[data-markdown-heading-id="${headingId}"]`
      : `[data-explorer-section="${sectionId}"]`;
    scrollWithin(readingMain, readingMain?.querySelector<HTMLElement>(selector));
  }

  function scrollWithin(container: HTMLElement | undefined, target: HTMLElement | null | undefined) {
    if (!container || !target) return;
    const containerRect = container.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const rawTop = targetRect.top - containerRect.top + container.scrollTop - 16;
    const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
    scrollReadingMainTo(Math.min(Math.max(0, rawTop), maxTop));
  }

  function scrollReadingMainTo(top: number, behavior: ScrollBehavior = 'smooth') {
    if (!readingMain) return;
    programmaticScrollUntil = performance.now() + (behavior === 'smooth' ? 900 : 120);
    lastKnownScrollTop = top;
    readingMain.scrollTo({ top, behavior });
  }

  function handleReadingScroll() {
    if (!readingMain || !browser) return;
    updateExplorerTargetFromScroll();
    if (performance.now() < programmaticScrollUntil) {
      lastKnownScrollTop = readingMain.scrollTop;
      return;
    }
    lastKnownScrollTop = readingMain.scrollTop;
  }

  function updateExplorerTargetFromScroll() {
    if (!readingMain) return;
    const containerTop = readingMain.getBoundingClientRect().top;
    const threshold = containerTop + 72;
    const sectionMarkers = Array.from(
      readingMain.querySelectorAll<HTMLElement>('[data-explorer-section]')
    );
    const headings = Array.from(
      readingMain.querySelectorAll<HTMLElement>('[data-markdown-heading-id]')
    );
    let activeSection = activeExplorerSection || 'problem';
    let activeHeading = '';

    for (const marker of sectionMarkers) {
      if (marker.getBoundingClientRect().top <= threshold) {
        activeSection = marker.dataset.explorerSection ?? activeSection;
      } else {
        break;
      }
    }

    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= threshold) {
        activeHeading = heading.dataset.markdownHeadingId ?? '';
      } else {
        break;
      }
    }

    activeExplorerSection = activeSection;
    activeExplorerHeadingId = activeHeading;
  }

  let problemId = $derived(`${track.slug}/${problem.slug}`);
  let isComplete = $state(false);
  let completedAt = $state<number | null>(null);
  let isMarking = $state(false);
  let lastSeenProblemId = $state<string | null>(null);

  onMount(() => {
    const savedMode = localStorage.getItem('reading-mode');
    if (savedMode === 'page' || savedMode === 'focus') readingMode = savedMode;

    isComplete = initiallyCompleted;
    completedAt = initiallyCompleted ? Date.now() : null;
    lastSeenProblemId = problemId;
    lastKnownScrollTop = readingMain?.scrollTop ?? 0;
    tick().then(updateExplorerTargetFromScroll);
    void loadCompletion(problemId);
  });

  $effect(() => {
    const pid = problemId;
    if (pid === lastSeenProblemId) return;
    lastSeenProblemId = pid;
    isComplete = false;
    completedAt = null;
    activeExplorerSection = 'problem';
    activeExplorerHeadingId = '';
    activeFocusIndex = 0;
    void loadCompletion(pid);
  });

  async function loadCompletion(pid: string) {
    if (!browser) return;
    try {
      const { readingProgressService } = await import('$lib/services/index.js');
      isComplete = await readingProgressService.isCompleted(pid);
      if (isComplete) completedAt = Date.now();
    } catch {
      // non-fatal
    }
  }

  async function handleMarkComplete() {
    if (isComplete || isMarking || !browser) return;
    isMarking = true;
    try {
      const { readingProgressService } = await import('$lib/services/index.js');
      const { wasNew } = await readingProgressService.markComplete(problemId);
      isComplete = true;
      completedAt = Date.now();
      if (wasNew) onMarkedComplete?.();
    } finally {
      isMarking = false;
    }
  }
</script>

<div class="reading-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <main class="reading-main" bind:this={readingMain} onscroll={handleReadingScroll}>
    <div class="reading-modebar">
      <div class="modebar-title">
        <span>{track.title} &middot; Module {problem.order.toString().padStart(2, '0')}</span>
        <strong>{problem.title}</strong>
      </div>
      <div class="reading-mode-toggle" aria-label="Reading mode">
        <button
          class:active={readingMode === 'page'}
          aria-pressed={readingMode === 'page'}
          onclick={() => selectReadingMode('page')}
          title="Read as a full page"
        >
          Page
        </button>
        <button
          class:active={readingMode === 'focus'}
          aria-pressed={readingMode === 'focus'}
          onclick={() => selectReadingMode('focus')}
          title="Read one step at a time"
        >
          Focus
        </button>
      </div>
    </div>

    {#if readingMode === 'focus'}
      <div class="reading-layout">
        <CourseExplorer
          {track}
          currentSlug={problem.slug}
          sections={explorerSections}
          activeSectionId={focusActiveSection}
          activeHeadingId={focusActiveHeadingId}
          bind:open={explorerOpen}
          onsection={(sectionId) => setActiveFocusIndex(focusIndexForSection(sectionId))}
          onheading={(sectionId, headingId) => setActiveFocusIndex(focusIndexForHeading(sectionId, headingId))}
        />

        <GradualReadingView
          steps={gradualSteps}
          activeIndex={activeFocusIndex}
          trackSlug={track.slug}
          {prevProblem}
          {nextProblem}
          {isComplete}
          {isMarking}
          onIndexChange={setActiveFocusIndex}
          onMarkComplete={handleMarkComplete}
        />
      </div>
    {:else}
      <div class="reading-layout">
        <CourseExplorer
          {track}
          currentSlug={problem.slug}
          sections={explorerSections}
          activeSectionId={activeExplorerSection}
          activeHeadingId={activeExplorerHeadingId}
          bind:open={explorerOpen}
          onsection={(sectionId) => void scrollToExplorerTarget(sectionId)}
          onheading={(sectionId, headingId) => void scrollToExplorerTarget(sectionId, headingId)}
        />

        <article class="reading-article">
          <header class="reading-header" data-explorer-section="problem">
            <div class="reading-eyebrow">
              <span class="text-slate-500 font-mono text-xs">
                {track.title} &middot; Module {problem.order.toString().padStart(2, '0')}
              </span>
            </div>
            <h1 class="reading-title">{problem.title}</h1>
            <div class="reading-meta">
              <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
                {problem.difficulty}
              </span>
              <span class="text-xs text-slate-500">{problem.estimatedMinutes} min read</span>
              {#each problem.tags as tag}
                <span class="badge badge-blue">{tag}</span>
              {/each}
            </div>
            {#if problem.description}
              <p class="reading-description">{problem.description}</p>
            {/if}
          </header>

          <section class="reading-body">
            <MarkdownRenderer content={problem.tabs.problem} variant="reading" headingPrefix="problem" />
          </section>

          {#if hasTheory}
            <section class="reading-section" data-explorer-section="theory">
              <h2 class="reading-section-title">Deep dive</h2>
              <MarkdownRenderer content={problem.tabs.theory} variant="reading" headingPrefix="theory" />
            </section>
          {/if}

          {#if hasFurther}
            <section class="reading-section" data-explorer-section="tips">
              <h2 class="reading-section-title">Further reading</h2>
              <MarkdownRenderer content={problem.tabs.tips} variant="reading" headingPrefix="tips" />
            </section>
          {/if}

          <section class="reading-complete">
            {#if isComplete}
              <div class="complete-card done">
                <span class="complete-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                <div class="complete-body">
                  <div class="complete-title">Completed</div>
                  <div class="complete-sub">Counted toward your streak and progress.</div>
                </div>
              </div>
            {:else}
              <div class="complete-card">
                <div class="complete-body">
                  <div class="complete-title">Finished reading?</div>
                  <div class="complete-sub">Mark this module complete to count it toward your progress.</div>
                </div>
                <button
                  class="btn-primary"
                  onclick={handleMarkComplete}
                  disabled={isMarking}
                >
                  {isMarking ? 'Marking...' : 'Mark as complete'}
                </button>
              </div>
            {/if}
          </section>

          <footer class="reading-footer">
            <ProblemNav
              trackSlug={track.slug}
              {prevProblem}
              {nextProblem}
            />
          </footer>
        </article>
      </div>
    {/if}
  </main>
</div>

<style>
  .reading-shell {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
    overflow: hidden;
    overscroll-behavior: none;
    background: #0f1117;
  }

  .reading-main {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
  }

  .reading-modebar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    min-height: 54px;
    padding: 0.65rem 1.25rem;
    border-bottom: 1px solid #1e293b;
    background: rgba(15, 17, 23, 0.94);
    backdrop-filter: blur(10px);
  }

  .modebar-title {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .modebar-title span {
    color: #64748b;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .modebar-title strong {
    overflow: hidden;
    color: #e2e8f0;
    font-size: 0.9rem;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .reading-mode-toggle {
    display: inline-flex;
    flex-shrink: 0;
    gap: 0.2rem;
    padding: 0.2rem;
    border: 1px solid #263348;
    border-radius: 8px;
    background: #111827;
  }

  .reading-mode-toggle button {
    min-width: 74px;
    min-height: 32px;
    padding: 0.35rem 0.7rem;
    border: 0;
    border-radius: 6px;
    color: #94a3b8;
    font-size: 0.82rem;
    font-weight: 700;
    transition: background 140ms ease, color 140ms ease;
  }

  .reading-mode-toggle button:hover {
    color: #e2e8f0;
  }

  .reading-mode-toggle button.active {
    background: #1e293b;
    color: #f8fafc;
  }

  .reading-layout {
    min-height: 100%;
    display: flex;
    align-items: flex-start;
  }

  .reading-layout :global(.course-explorer) {
    position: sticky;
    top: 54px;
    height: calc(100vh - 110px);
  }

  .reading-layout :global(.gradual-reader) {
    flex: 1;
  }

  .reading-article {
    width: min(100%, 820px);
    max-width: 820px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  .reading-header {
    padding-bottom: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid #1e293b;
  }

  .reading-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
  }

  .reading-title {
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 1rem;
  }

  .reading-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.25rem;
  }

  .reading-description {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.6;
    margin: 0;
  }

  .reading-body :global(.prose),
  .reading-section :global(.prose) {
    padding-left: 0;
    padding-right: 0;
  }

  .reading-section {
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid #1e293b;
  }

  .reading-section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0 0 0.5rem;
    letter-spacing: 0;
  }

  .reading-footer {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid #1e293b;
  }

  .reading-complete {
    margin-top: 3rem;
  }

  .complete-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 8px;
  }

  .complete-card.done {
    border-color: rgba(96, 165, 250, 0.3);
    background: linear-gradient(180deg, rgba(96, 165, 250, 0.06), #131720);
  }

  .complete-body {
    flex: 1;
    min-width: 0;
  }

  .complete-title {
    color: #e2e8f0;
    font-weight: 600;
    font-size: 0.92rem;
  }

  .complete-sub {
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 0.15rem;
    line-height: 1.4;
  }

  .complete-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 999px;
    background: rgba(96, 165, 250, 0.18);
    color: #60a5fa;
    flex-shrink: 0;
  }

  @media (max-width: 720px) {
    .reading-modebar {
      align-items: stretch;
      flex-direction: column;
      padding: 0.75rem 1rem;
    }

    .reading-mode-toggle {
      width: 100%;
    }

    .reading-mode-toggle button {
      flex: 1;
    }
  }
</style>
