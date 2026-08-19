<script lang="ts">
  /**
   * FlashcardsView
   *
   * Full-page layout for a `flashcards` module: a deck dashboard, a review
   * session driven by the shared scheduler, and a session summary. Card
   * scheduling state is written one review at a time, so quitting halfway
   * never loses work.
   */
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import Header from '$lib/components/Header.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import FlashcardStage from '$lib/components/FlashcardStage.svelte';
  import { buildQueue, formatDueIn, freshState, gradePreview } from '$lib/flashcards/scheduler.js';
  import type {
    Flashcard,
    FlashcardCardState,
    FlashcardDeck,
    FlashcardGrade,
    FlashcardProgress,
    Problem,
    ProblemMeta,
    Track
  } from '$lib/types/course.js';

  interface Props {
    track: Track;
    problem: Problem;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
    deck: FlashcardDeck;
    initiallyCompleted?: boolean;
    initialProgress?: FlashcardProgress | null;
    onDeckLearned?: (total: number) => void;
  }

  type Phase = 'intro' | 'reviewing' | 'summary';

  let {
    track,
    problem,
    prevProblem,
    nextProblem,
    deck,
    initiallyCompleted = false,
    initialProgress = null,
    onDeckLearned
  }: Props = $props();

  let phase = $state<Phase>('intro');
  let progress = $state<FlashcardProgress | null>(null);
  let isComplete = $state(false);
  let queue = $state<Flashcard[]>([]);
  let queueIndex = $state(0);
  let revealed = $state(false);
  let cardShownAt = $state(0);
  let tallies = $state<Record<FlashcardGrade, number>>({ again: 0, hard: 0, good: 0, easy: 0 });
  let sessionReviews = $state(0);
  let inFlight = $state(0);
  let saveFailed = $state(false);
  // Responses can land out of order because grading does not await the write.
  // Only apply a response newer than the newest already applied.
  let reviewSeq = 0;
  let appliedSeq = 0;
  let lastSeenProblemId = $state('');
  let confirmingReset = $state(false);

  let problemId = $derived(`${track.slug}/${problem.slug}`);
  let cards = $derived(deck.cards ?? []);
  let currentCard = $derived(queue[queueIndex] ?? null);
  let stateMap = $derived(new Map((progress?.states ?? []).map((s) => [s.cardId, s])));
  let currentState = $derived<FlashcardCardState>(
    currentCard ? stateMap.get(currentCard.id) ?? freshState(currentCard.id) : freshState('')
  );
  let preview = $derived(gradePreview(currentState));
  let learnedPct = $derived(
    cards.length === 0 ? 0 : Math.round(((progress?.learned ?? 0) / cards.length) * 100)
  );

  onMount(() => {
    if (!browser) return;
    progress = initialProgress;
    isComplete = initiallyCompleted;
    lastSeenProblemId = problemId;
  });

  // Navigating between two flashcard modules reuses this component, so reset
  // everything when the underlying module changes.
  $effect(() => {
    const pid = problemId;
    if (!lastSeenProblemId || pid === lastSeenProblemId) return;
    lastSeenProblemId = pid;
    phase = 'intro';
    progress = initialProgress;
    isComplete = initiallyCompleted;
    queue = [];
    queueIndex = 0;
    revealed = false;
    confirmingReset = false;
    resetTallies();
    void refreshProgress();
  });

  function resetTallies() {
    tallies = { again: 0, hard: 0, good: 0, easy: 0 };
    sessionReviews = 0;
  }

  async function refreshProgress() {
    try {
      const { flashcardService } = await import('$lib/services/index.js');
      progress = await flashcardService.getProgress(problemId);
      isComplete = progress.hasPassed;
    } catch {
      // Non-fatal: the deck still works, it just will not show saved counts.
    }
  }

  function startSession(mode: 'scheduled' | 'cram') {
    if (cards.length === 0) return;
    // Nothing is due and nothing is new, so the scheduled queue would be
    // empty. The button says "review anyway"; honour it.
    if (mode === 'scheduled' && scheduledCount === 0) mode = 'cram';
    const states = progress?.states ?? [];
    const built = buildQueue(cards, states, {
      newPerSession: deck.newPerSession,
      maxPerSession: deck.maxPerSession,
      includeAll: mode === 'cram'
    });
    if (built.length === 0) return;
    queue = built;
    queueIndex = 0;
    revealed = false;
    resetTallies();
    saveFailed = false;
    cardShownAt = Date.now();
    phase = 'reviewing';
  }

  function reveal() {
    if (phase !== 'reviewing' || revealed) return;
    revealed = true;
  }

  async function grade(g: FlashcardGrade) {
    if (phase !== 'reviewing' || !revealed || !currentCard) return;
    const card = currentCard;
    const responseMs = Math.max(0, Date.now() - cardShownAt);

    tallies = { ...tallies, [g]: tallies[g] + 1 };
    sessionReviews += 1;

    // A forgotten card goes back to the end of this sitting's queue, which is
    // what makes a single session actually teach rather than just measure.
    const requeue = g === 'again';

    advance(requeue ? card : null);

    if (!browser) return;
    const seq = ++reviewSeq;
    inFlight += 1;
    try {
      const { flashcardService } = await import('$lib/services/index.js');
      const result = await flashcardService.review(problemId, {
        cardId: card.id,
        grade: g,
        responseMs
      });
      if (result) {
        if (seq > appliedSeq) {
          appliedSeq = seq;
          progress = result.progress;
        }
        if (result.wasNewCompletion) {
          isComplete = true;
          onDeckLearned?.(cards.length);
        }
      } else {
        saveFailed = true;
      }
    } catch {
      saveFailed = true;
    } finally {
      inFlight -= 1;
    }
  }

  function advance(requeueCard: Flashcard | null) {
    if (requeueCard) queue = [...queue, requeueCard];
    if (queueIndex >= queue.length - 1) {
      phase = 'summary';
      revealed = false;
      return;
    }
    queueIndex += 1;
    revealed = false;
    cardShownAt = Date.now();
  }

  function endSession() {
    phase = 'summary';
    revealed = false;
    void refreshProgress();
  }

  async function doReset() {
    confirmingReset = false;
    try {
      const { flashcardService } = await import('$lib/services/index.js');
      const next = await flashcardService.reset(problemId);
      if (next) progress = next;
    } catch {
      // Non-fatal.
    }
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
    // Anything the browser already has a keyboard behaviour for handles its
    // own keys: fields, and every focusable control. Without this, Enter on a
    // link and Space on a button are swallowed and the page becomes a
    // keyboard trap.
    const target = e.target as HTMLElement | null;
    if (
      target &&
      (target.isContentEditable ||
        target.closest('input, textarea, select, button, a, [contenteditable], [role="textbox"]'))
    ) {
      return;
    }

    if (phase === 'intro' && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      startSession('scheduled');
      return;
    }
    if (phase !== 'reviewing') return;

    if (!revealed && (e.key === ' ' || e.key === 'Enter')) {
      e.preventDefault();
      reveal();
    } else if (revealed && ['1', '2', '3', '4'].includes(e.key)) {
      e.preventDefault();
      const grades: FlashcardGrade[] = ['again', 'hard', 'good', 'easy'];
      void grade(grades[Number(e.key) - 1]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      endSession();
    }
  }

  let scheduledCount = $derived(
    Math.min(
      (progress?.due ?? 0) + Math.min(progress?.fresh ?? cards.length, deck.newPerSession ?? 15),
      deck.maxPerSession ?? 60
    )
  );
</script>

<svelte:window onkeydown={onKeydown} />

<div class="deck-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <main class="deck-main">
    <article class="deck-article">
      <header class="deck-header">
        <div class="deck-eyebrow">
          Flashcards · {track.title} · Module {problem.order.toString().padStart(2, '0')}
        </div>
        <h1>{deck.title ?? problem.title}</h1>
        <div class="deck-meta">
          <span class="badge badge-blue">{cards.length} cards</span>
          {#if (progress?.due ?? 0) > 0}
            <span class="badge badge-yellow">{progress?.due} due</span>
          {/if}
          {#if (progress?.fresh ?? 0) > 0}
            <span class="badge badge-blue">{progress?.fresh} new</span>
          {/if}
          {#if isComplete}<span class="badge badge-green">Deck learned</span>{/if}
        </div>
        {#if problem.description}<p>{problem.description}</p>{/if}
      </header>

      {#if phase === 'intro'}
        {#if problem.tabs.problem.trim()}
          <section class="deck-copy">
            <MarkdownRenderer content={problem.tabs.problem} variant="study" />
          </section>
        {/if}

        {#if deck.instructions}
          <section class="deck-instructions">
            <MarkdownRenderer content={deck.instructions} variant="compact" />
          </section>
        {/if}

        <section class="deck-card">
          <div class="progress-track" aria-hidden="true">
            <div class="progress-fill" style="width: {learnedPct}%"></div>
          </div>
          <div class="stats-grid">
            <div>
              <span class="stat-value">{progress?.learned ?? 0} / {cards.length}</span>
              <span class="stat-label">Learned</span>
            </div>
            <div>
              <span class="stat-value">{progress?.due ?? 0}</span>
              <span class="stat-label">Due now</span>
            </div>
            <div>
              <span class="stat-value">{progress?.fresh ?? cards.length}</span>
              <span class="stat-label">Never seen</span>
            </div>
            <div>
              <span class="stat-value">{progress?.reviews ?? 0}</span>
              <span class="stat-label">Total reviews</span>
            </div>
          </div>

          <div class="button-row">
            <button class="cta-primary" onclick={() => startSession('scheduled')} disabled={cards.length === 0}>
              {scheduledCount > 0 ? `Review ${scheduledCount} cards` : 'Nothing due — review anyway'}
            </button>
            <button class="cta-secondary" onclick={() => startSession('cram')} disabled={cards.length === 0}>
              Cram all {cards.length}
            </button>
          </div>

          <p class="hint">
            {#if (progress?.due ?? 0) === 0 && progress?.nextDueAt}
              Next card falls due {formatDueIn(progress.nextDueAt)}.
            {:else}
              <kbd>Space</kbd> flips · <kbd>1</kbd>–<kbd>4</kbd> grade · <kbd>Esc</kbd> ends the session.
            {/if}
            <a class="review-link" href="/review">Review every deck →</a>
          </p>

          {#if (progress?.reviews ?? 0) > 0}
            <div class="reset-row">
              {#if confirmingReset}
                <span>Forget all scheduling for this deck?</span>
                <button class="link-button danger" onclick={doReset}>Yes, reset</button>
                <button class="link-button" onclick={() => (confirmingReset = false)}>Cancel</button>
              {:else}
                <button class="link-button" onclick={() => (confirmingReset = true)}>Reset deck progress</button>
              {/if}
            </div>
          {/if}
        </section>
      {:else if phase === 'reviewing' && currentCard}
        <div class="session-bar">
          <span>{queueIndex + 1} / {queue.length}</span>
          <span class="session-tallies">
            <span class="tally-again">{tallies.again} again</span>
            <span class="tally-good">{tallies.good + tallies.easy} recalled</span>
          </span>
          <button class="link-button" onclick={endSession}>End session <kbd>Esc</kbd></button>
        </div>

        {#key currentCard.id}
          <FlashcardStage
            card={currentCard}
            {revealed}
            {preview}
            positionLabel={`Card ${queueIndex + 1} of ${queue.length}`}
            isNew={currentState.lastReviewedAt === null}
            onReveal={reveal}
            onGrade={grade}
          />
        {/key}

        {#if saveFailed}
          <p class="save-warning">Could not save the last review. Your session keeps going, but progress may not persist.</p>
        {:else if inFlight > 0}
          <p class="save-note">Saving…</p>
        {/if}
      {:else if phase === 'summary'}
        <section class="results-card">
          <div>
            <div class="result-kicker">Session complete</div>
            <h2>{sessionReviews} reviews</h2>
            <p>
              {tallies.again} again · {tallies.hard} hard · {tallies.good} good · {tallies.easy} easy
            </p>
            <p class="muted">
              {progress?.learned ?? 0} of {cards.length} cards learned.
              {#if (progress?.due ?? 0) > 0}
                {progress?.due} still due now.
              {:else if progress?.nextDueAt}
                Next card due {formatDueIn(progress.nextDueAt)}.
              {/if}
            </p>
          </div>
          <div class="button-row">
            <button class="cta-primary" onclick={() => startSession('scheduled')}>Another round</button>
            <button class="cta-secondary" onclick={() => (phase = 'intro')}>Back to deck</button>
          </div>
        </section>

        {#if problem.tabs.tips.trim()}
          <section class="deck-copy">
            <MarkdownRenderer content={problem.tabs.tips} variant="study" />
          </section>
        {/if}
      {/if}

      {#if phase !== 'reviewing' && problem.tabs.theory.trim()}
        <details class="theory-details">
          <summary>Notes behind this deck</summary>
          <MarkdownRenderer content={problem.tabs.theory} variant="study" />
        </details>
      {/if}

      <ProblemNav {prevProblem} {nextProblem} trackSlug={track.slug} />
    </article>
  </main>
</div>

<style>
  .deck-shell {
    min-height: 100%;
    background: #0f1117;
    color: #e2e8f0;
  }
  .deck-main {
    max-width: 900px;
    margin: 0 auto;
    padding: 1.5rem;
  }
  .deck-article {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .deck-header {
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1rem;
  }
  .deck-eyebrow {
    color: #60a5fa;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  h1 {
    font-size: 2rem;
    margin: 0.35rem 0;
  }
  .deck-meta, .button-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    flex-wrap: wrap;
  }
  .deck-card, .results-card, .deck-instructions {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem;
  }
  .deck-instructions {
    border-left: 3px solid #3b82f6;
  }
  .progress-track {
    height: 6px;
    border-radius: 999px;
    background: #1e293b;
    overflow: hidden;
    margin-bottom: 1rem;
  }
  .progress-fill {
    height: 100%;
    background: #22c55e;
    transition: width 200ms ease;
  }
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  .stats-grid > div {
    background: #0f1117;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.8rem;
  }
  .stat-value {
    display: block;
    font-size: 1.3rem;
    font-weight: 800;
    color: #f8fafc;
  }
  .stat-label, .hint, .muted {
    color: #94a3b8;
    font-size: 0.78rem;
  }
  .hint {
    margin: 0.9rem 0 0;
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    align-items: center;
  }
  .review-link {
    color: #60a5fa;
    text-decoration: none;
  }
  .review-link:hover {
    text-decoration: underline;
  }
  .cta-primary, .cta-secondary {
    border-radius: 8px;
    padding: 0.65rem 1rem;
    font-weight: 700;
    cursor: pointer;
  }
  .cta-primary {
    background: #2563eb;
    border: 1px solid #3b82f6;
    color: white;
  }
  .cta-primary:hover:not(:disabled) {
    background: #1d4ed8;
  }
  .cta-secondary {
    background: transparent;
    border: 1px solid #334155;
    color: #cbd5e1;
  }
  .cta-secondary:hover:not(:disabled) {
    border-color: #64748b;
  }
  .cta-primary:disabled, .cta-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .session-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    color: #94a3b8;
    font-size: 0.82rem;
    flex-wrap: wrap;
  }
  .session-tallies {
    display: flex;
    gap: 0.8rem;
  }
  .tally-again { color: #fca5a5; }
  .tally-good { color: #86efac; }
  .link-button {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.82rem;
    padding: 0;
  }
  .link-button:hover {
    color: #e2e8f0;
  }
  .link-button.danger {
    color: #f87171;
  }
  .reset-row {
    margin-top: 1rem;
    padding-top: 0.9rem;
    border-top: 1px solid #1e293b;
    display: flex;
    gap: 0.8rem;
    align-items: center;
    flex-wrap: wrap;
    color: #94a3b8;
    font-size: 0.82rem;
  }
  .results-card {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .result-kicker {
    color: #4ade80;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  h2 {
    margin: 0.25rem 0;
    font-size: 1.8rem;
  }
  .save-warning {
    color: #fca5a5;
    font-size: 0.82rem;
  }
  .save-note {
    color: #64748b;
    font-size: 0.78rem;
  }
  .theory-details {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  .theory-details summary {
    cursor: pointer;
    font-weight: 700;
    color: #cbd5e1;
  }
  kbd {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.05rem 0.3rem;
    font-size: 0.7rem;
  }
  @media (max-width: 680px) {
    .stats-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
