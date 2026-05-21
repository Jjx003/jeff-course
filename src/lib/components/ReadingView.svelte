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
  import ReadingAudioPlayer from '$lib/components/ReadingAudioPlayer.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import { buildGradualReadSteps } from '$lib/reading/gradualReader.js';
  import type { ReadingAudioClip, ReadingAudioManifest } from '$lib/types/audio.js';
  import type { Problem, ProblemMeta, Track } from '$lib/types/course.js';

  interface DomWordToken {
    node: Text;
    start: number;
    end: number;
    value: string;
  }

  interface CssHighlightsApi {
    highlights?: {
      set: (name: string, highlight: unknown) => void;
      delete: (name: string) => boolean;
    };
  }

  interface WindowWithHighlight extends Window {
    Highlight?: new (...ranges: Range[]) => unknown;
  }

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
  const PAGE_AUDIO_COMPACT_ON_SCROLL = 260;
  const PAGE_AUDIO_COMPACT_OFF_SCROLL = 90;

  let hasTheory = $derived(problem.tabs.theory.trim().length > 0);
  let hasFurther = $derived(problem.tabs.tips.trim().length > 0);
  let readingMain = $state<HTMLElement | undefined>(undefined);
  let explorerOpen = $state(true);
  let activeExplorerSection = $state('problem');
  let readingMode = $state<'page' | 'focus'>('page');
  let activeFocusIndex = $state(0);
  let pageAudioCompact = $state(false);
  const audioWordHighlightName = 'reading-audio-word';
  let lastAudioFollowAt = 0;
  let suppressAudioFollowUntil = 0;
  let programmaticScrollUntil = 0;
  let lastKnownScrollTop = 0;
  let lastPageAudioClipId: string | null = null;

  let explorerSections = $derived.by<ExplorerSection[]>(() => [
    { id: 'problem', label: 'Overview', content: problem.tabs.problem },
    ...(hasTheory ? [{ id: 'theory', label: 'Deep dive', content: problem.tabs.theory }] : []),
    ...(hasFurther ? [{ id: 'tips', label: 'Further reading', content: problem.tabs.tips }] : [])
  ]);
  let gradualSteps = $derived(buildGradualReadSteps(explorerSections));
  let focusActiveSection = $derived(gradualSteps[activeFocusIndex]?.sectionId ?? 'problem');
  let audioManifest = $state<ReadingAudioManifest>({ available: false, title: null, clips: [] });

  let focusAudioClips = $derived.by<ReadingAudioClip[]>(() => {
    const sectionCounts = new Map<string, number>();
    return gradualSteps.map((step) => {
      const nextIndex = (sectionCounts.get(step.sectionId) ?? 0) + 1;
      sectionCounts.set(step.sectionId, nextIndex);
      const realClip = audioManifest.clips.find(
        (clip) => clip.sectionId === step.sectionId && clip.stepIndex === nextIndex
      );
      return {
        id: realClip?.id ?? `stub-${step.id}`,
        title: realClip?.title ?? `${step.sectionLabel} - ${step.title}`,
        sectionId: step.sectionId,
        stepIndex: nextIndex,
        durationMs: realClip?.durationMs ?? estimateDuration(step.content),
        url: realClip?.url ?? null,
        text: realClip?.text ?? plainText(step.content),
        words: realClip?.words
      };
    });
  });

  let pageAudioClips = $derived.by<ReadingAudioClip[]>(() => {
    if (audioManifest.clips.length > 0) return audioManifest.clips;
    return explorerSections.map((section, index) => ({
      id: `stub-page-${section.id}`,
      title: section.label,
      sectionId: section.id,
      stepIndex: index + 1,
      durationMs: estimateDuration(section.content),
      url: null,
      text: plainText(section.content)
    }));
  });

  let pageSectionClipCounts = $derived.by(() => {
    const counts = new Map<string, number>();
    for (const clip of pageAudioClips) counts.set(clip.sectionId, (counts.get(clip.sectionId) ?? 0) + 1);
    return counts;
  });

  function selectReadingMode(mode: 'page' | 'focus') {
    readingMode = mode;
    if (mode === 'focus') pageAudioCompact = false;
    if (browser) localStorage.setItem('reading-mode', mode);
  }

  function setActiveFocusIndex(index: number) {
    activeFocusIndex = index;
    scrollReadingMainTo(0, 'smooth', 'navigation');
    clearAudioWordHighlight();
  }

  function plainText(markdown: string): string {
    return markdown
      .replace(/```[\s\S]*?```/g, ' ')
      .replace(/!\[[^\]]*]\([^)]*\)/g, ' ')
      .replace(/\[([^\]]+)]\([^)]*\)/g, '$1')
      .replace(/[`*_~>#-]/g, ' ')
      .replace(/\$+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function estimateDuration(markdown: string): number {
    const words = plainText(markdown).split(/\s+/).filter(Boolean).length;
    return Math.max(5000, Math.round((words / 150) * 60_000));
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
    scrollReadingMainTo(Math.min(Math.max(0, rawTop), maxTop), 'smooth', 'navigation');
  }

  async function handlePageAudioClipChange(clip: ReadingAudioClip) {
    activeExplorerSection = clip.sectionId;
    if (clip.id === lastPageAudioClipId) return;
    lastPageAudioClipId = clip.id;
    await tick();
    const target = readingMain?.querySelector<HTMLElement>(`[data-audio-section="${clip.sectionId}"]`);
    if (!readingMain || !target) return;
    const total = pageSectionClipCounts.get(clip.sectionId) ?? 1;
    const ratio = total <= 1 ? 0 : Math.max(0, Math.min(1, (clip.stepIndex - 1) / total));
    const containerRect = readingMain.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const rawTop = targetRect.top - containerRect.top + readingMain.scrollTop - 18;
    const sectionOffset = Math.max(0, target.scrollHeight - readingMain.clientHeight * 0.45) * ratio;
    const maxTop = Math.max(0, readingMain.scrollHeight - readingMain.clientHeight);
    scrollReadingMainTo(Math.min(Math.max(0, rawTop + sectionOffset), maxTop), 'smooth', 'audio');
  }

  function scrollReadingMainTo(
    top: number,
    behavior: ScrollBehavior = 'smooth',
    source: 'audio' | 'navigation' | 'follow' = 'navigation'
  ) {
    if (!readingMain) return;
    programmaticScrollUntil = performance.now() + (behavior === 'smooth' ? 900 : 120);
    if (source === 'navigation') suppressAudioFollowUntil = performance.now() + 900;
    lastKnownScrollTop = top;
    readingMain.scrollTo({ top, behavior });
  }

  function floatingAudioInsets(containerRect: DOMRect): { top: number; bottom: number } {
    const player =
      readingMode === 'focus'
        ? readingMain?.querySelector<HTMLElement>('.gradual-reader .audio-player')
        : readingMain?.querySelector<HTMLElement>('.reading-audio .audio-player');
    if (!player) return { top: 0, bottom: 0 };
    const playerRect = player.getBoundingClientRect();
    const midpoint = containerRect.top + containerRect.height / 2;
    return {
      top: playerRect.top < midpoint ? Math.max(0, playerRect.bottom - containerRect.top + 16) : 0,
      bottom: playerRect.top >= midpoint ? Math.max(0, containerRect.bottom - playerRect.top + 16) : 0
    };
  }

  function normalizeAudioWord(value: string): string {
    return value
      .toLocaleLowerCase()
      .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '')
      .replace(/[\u2019']/g, "'");
  }

  function collectDomWords(root: HTMLElement): DomWordToken[] {
    const words: DomWordToken[] = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest('script, style, button, input, textarea, select')) {
          return NodeFilter.FILTER_REJECT;
        }
        return node.textContent?.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });

    const wordPattern = /[\p{L}\p{N}]+(?:[\u2019'][\p{L}\p{N}]+)?/gu;
    let node = walker.nextNode() as Text | null;
    while (node) {
      const text = node.textContent ?? '';
      for (const match of text.matchAll(wordPattern)) {
        const value = normalizeAudioWord(match[0]);
        if (value) {
          words.push({
            node,
            start: match.index ?? 0,
            end: (match.index ?? 0) + match[0].length,
            value
          });
        }
      }
      node = walker.nextNode() as Text | null;
    }
    return words;
  }

  function scoreDomWordCandidate(
    domWords: DomWordToken[],
    clipWords: string[],
    domIndex: number,
    wordIndex: number
  ): number {
    let score = 0;
    for (let offset = -5; offset <= 5; offset += 1) {
      const clipWord = clipWords[wordIndex + offset];
      const domWord = domWords[domIndex + offset]?.value;
      if (!clipWord || !domWord) continue;
      if (clipWord === domWord) score += offset === 0 ? 4 : 1;
    }
    return score;
  }

  function findAudioWordToken(root: HTMLElement, clip: ReadingAudioClip, wordIndex: number): DomWordToken | null {
    const words = clip.words ?? [];
    const activeWord = words[wordIndex];
    if (!activeWord) return null;

    const domWords = collectDomWords(root);
    const clipWords = words.map((word) => normalizeAudioWord(word.text));
    const target = clipWords[wordIndex];
    if (!target) return null;

    let bestToken: DomWordToken | null = null;
    let bestScore = -1;
    for (let index = 0; index < domWords.length; index += 1) {
      if (domWords[index].value !== target) continue;
      const score = scoreDomWordCandidate(domWords, clipWords, index, wordIndex);
      if (score > bestScore) {
        bestScore = score;
        bestToken = domWords[index];
      }
    }
    return bestToken;
  }

  function highlightAudioWord(root: HTMLElement, clip: ReadingAudioClip, wordIndex: number): Range | null {
    const api = CSS as CssHighlightsApi;
    const HighlightCtor = (window as WindowWithHighlight).Highlight;
    if (!api.highlights || !HighlightCtor) return null;

    const token = findAudioWordToken(root, clip, wordIndex);
    if (!token) {
      clearAudioWordHighlight();
      return null;
    }

    const range = document.createRange();
    range.setStart(token.node, token.start);
    range.setEnd(token.node, token.end);
    api.highlights.set(audioWordHighlightName, new HighlightCtor(range));
    return range;
  }

  function clearAudioWordHighlight() {
    const api = CSS as CssHighlightsApi;
    api.highlights?.delete(audioWordHighlightName);
  }

  function maybeFollowAudioWord(range: Range) {
    if (!readingMain) return;

    const now = performance.now();
    if (now < suppressAudioFollowUntil || now - lastAudioFollowAt < 850) return;

    const wordRect = range.getBoundingClientRect();
    const viewportRect = readingMain.getBoundingClientRect();
    if (wordRect.width === 0 && wordRect.height === 0) return;

    const audioInsets = floatingAudioInsets(viewportRect);
    const upperBand = Math.max(viewportRect.top + viewportRect.height * 0.24, viewportRect.top + audioInsets.top);
    const lowerBand = Math.min(
      viewportRect.top + viewportRect.height * 0.7,
      viewportRect.bottom - audioInsets.bottom
    );
    const isComfortablyVisible = wordRect.top >= upperBand && wordRect.bottom <= lowerBand;
    if (isComfortablyVisible) return;

    const targetOffset = wordRect.top < upperBand ? viewportRect.height * 0.34 : viewportRect.height * 0.48;
    const desiredTop = readingMain.scrollTop + wordRect.top - viewportRect.top - targetOffset;
    const maxTop = Math.max(0, readingMain.scrollHeight - readingMain.clientHeight);
    lastAudioFollowAt = now;
    scrollReadingMainTo(Math.min(Math.max(0, desiredTop), maxTop), 'smooth', 'follow');
  }

  function handleAudioWordChange(clip: ReadingAudioClip, _clipIndex: number, wordIndex: number) {
    if (!browser || wordIndex < 0) {
      clearAudioWordHighlight();
      return;
    }

    const root =
      readingMode === 'focus'
        ? readingMain?.querySelector<HTMLElement>('.reader-card')
        : readingMain?.querySelector<HTMLElement>(`[data-audio-section="${clip.sectionId}"]`);
    if (!root) return;
    const range = highlightAudioWord(root, clip, wordIndex);
    if (range) maybeFollowAudioWord(range);
  }

  function handleReadingScroll() {
    if (!readingMain || !browser) return;
    if (readingMode !== 'page') {
      pageAudioCompact = false;
    } else if (!pageAudioCompact && readingMain.scrollTop > PAGE_AUDIO_COMPACT_ON_SCROLL) {
      pageAudioCompact = true;
    } else if (pageAudioCompact && readingMain.scrollTop < PAGE_AUDIO_COMPACT_OFF_SCROLL) {
      pageAudioCompact = false;
    }
    if (performance.now() < programmaticScrollUntil) {
      lastKnownScrollTop = readingMain.scrollTop;
      return;
    }
    const delta = Math.abs(readingMain.scrollTop - lastKnownScrollTop);
    lastKnownScrollTop = readingMain.scrollTop;
    if (delta > 4) suppressAudioFollowUntil = performance.now() + 1400;
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
    void loadCompletion(problemId);
    void loadAudioManifest(track.slug, problem.slug);
    return () => clearAudioWordHighlight();
  });

  $effect(() => {
    const pid = problemId;
    if (pid === lastSeenProblemId) return;
    lastSeenProblemId = pid;
    isComplete = false;
    completedAt = null;
    activeExplorerSection = 'problem';
    activeFocusIndex = 0;
    lastPageAudioClipId = null;
    clearAudioWordHighlight();
    void loadCompletion(pid);
    void loadAudioManifest(track.slug, problem.slug);
  });

  async function loadAudioManifest(trackSlug: string, problemSlug: string) {
    if (!browser) return;
    try {
      const response = await fetch(`/api/audio/${trackSlug}/${problemSlug}`);
      if (!response.ok) throw new Error('Audio manifest unavailable');
      audioManifest = (await response.json()) as ReadingAudioManifest;
    } catch {
      audioManifest = { available: false, title: null, clips: [] };
    }
  }

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
          bind:open={explorerOpen}
          onsection={(sectionId) => setActiveFocusIndex(focusIndexForSection(sectionId))}
          onheading={(sectionId, headingId) => setActiveFocusIndex(focusIndexForHeading(sectionId, headingId))}
        />

        <GradualReadingView
          steps={gradualSteps}
          activeIndex={activeFocusIndex}
          audioClips={focusAudioClips}
          trackSlug={track.slug}
          {prevProblem}
          {nextProblem}
          {isComplete}
          {isMarking}
          onIndexChange={setActiveFocusIndex}
          onMarkComplete={handleMarkComplete}
          onAudioWordChange={handleAudioWordChange}
        />
      </div>
    {:else}
      <div class="reading-layout">
        <CourseExplorer
          {track}
          currentSlug={problem.slug}
          sections={explorerSections}
          activeSectionId={activeExplorerSection}
          bind:open={explorerOpen}
          onsection={(sectionId) => void scrollToExplorerTarget(sectionId)}
          onheading={(sectionId, headingId) => void scrollToExplorerTarget(sectionId, headingId)}
        />

        <article class="reading-article">
          <div class="reading-audio">
            <ReadingAudioPlayer
              clips={pageAudioClips}
              compact={pageAudioCompact}
              storageKey={`${problemId}:page`}
              onClipChange={(clip) => void handlePageAudioClipChange(clip)}
              onWordChange={handleAudioWordChange}
            />
          </div>

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

          <section class="reading-body" data-audio-section="problem">
            <MarkdownRenderer content={problem.tabs.problem} variant="reading" headingPrefix="problem" />
          </section>

          {#if hasTheory}
            <section class="reading-section" data-explorer-section="theory" data-audio-section="theory">
              <h2 class="reading-section-title">Deep dive</h2>
              <MarkdownRenderer content={problem.tabs.theory} variant="reading" headingPrefix="theory" />
            </section>
          {/if}

          {#if hasFurther}
            <section class="reading-section" data-explorer-section="tips" data-audio-section="tips">
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

  .reading-layout :global(.gradual-reader .audio-player) {
    position: sticky;
    top: 66px;
    z-index: 15;
    backdrop-filter: blur(12px);
  }

  .reading-article {
    width: min(100%, 820px);
    max-width: 820px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  .reading-audio {
    position: sticky;
    top: 66px;
    z-index: 15;
    min-height: 10.75rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
  }

  .reading-audio :global(.audio-player) {
    position: static;
  }

  :global(::highlight(reading-audio-word)) {
    background: rgba(56, 189, 248, 0.28);
    color: #f8fafc;
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

    .reading-layout :global(.gradual-reader .audio-player),
    .reading-audio {
      top: 118px;
    }
  }
</style>
