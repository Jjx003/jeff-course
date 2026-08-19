<script lang="ts">
  /**
   * /review — the cross-course spaced-repetition queue.
   *
   * Every flashcards module in every enrolled track contributes here. This is
   * the page a learner opens daily; individual deck pages are for working
   * through a topic the first time.
   */
  import Header from '$lib/components/Header.svelte';
  import FlashcardStage from '$lib/components/FlashcardStage.svelte';
  import { freshState, gradePreview } from '$lib/flashcards/scheduler.js';
  import type { FlashcardGrade } from '$lib/types/course.js';
  import type { PageData } from './$types';
  import type { ReviewQueueItem } from './+page.server';

  let { data }: { data: PageData } = $props();

  type Phase = 'intro' | 'reviewing' | 'summary';

  // The server already trimmed the queues to what a sitting can use; this is
  // only for the copy that explains the cap.
  let newCardAllowance = $derived(data.newCardAllowance);

  let phase = $state<Phase>('intro');
  let queue = $state<ReviewQueueItem[]>([]);
  let index = $state(0);
  let revealed = $state(false);
  let shownAt = $state(0);
  let tallies = $state<Record<FlashcardGrade, number>>({ again: 0, hard: 0, good: 0, easy: 0 });
  let reviewed = $state(0);
  let saveFailed = $state(false);

  let summary = $derived(data.summary);
  let totalDue = $derived(summary.reduce((n, d) => n + d.due, 0));
  let totalFresh = $derived(summary.reduce((n, d) => n + d.fresh, 0));
  let totalCards = $derived(summary.reduce((n, d) => n + d.totalCards, 0));
  let totalLearned = $derived(summary.reduce((n, d) => n + d.learned, 0));
  let current = $derived(queue[index] ?? null);
  let preview = $derived(
    gradePreview(current?.state ?? freshState(current?.card.id ?? ''))
  );
  let sessionSize = $derived(data.due.length + data.fresh.length);

  function start(includeNew: boolean) {
    const built = includeNew ? [...data.due, ...data.fresh] : [...data.due];
    if (built.length === 0) return;
    queue = built;
    index = 0;
    revealed = false;
    tallies = { again: 0, hard: 0, good: 0, easy: 0 };
    reviewed = 0;
    saveFailed = false;
    shownAt = Date.now();
    phase = 'reviewing';
  }

  async function grade(g: FlashcardGrade) {
    if (!current || !revealed) return;
    const item = current;
    const responseMs = Math.max(0, Date.now() - shownAt);
    tallies = { ...tallies, [g]: tallies[g] + 1 };
    reviewed += 1;

    // Forgotten cards come back later in the same sitting.
    if (g === 'again') queue = [...queue, item];

    if (index >= queue.length - 1) {
      phase = 'summary';
      revealed = false;
    } else {
      index += 1;
      revealed = false;
      shownAt = Date.now();
    }

    try {
      const { flashcardService } = await import('$lib/services/index.js');
      const result = await flashcardService.review(item.problemId, {
        cardId: item.card.id,
        grade: g,
        responseMs
      });
      if (!result) {
        saveFailed = true;
      } else {
        // Refresh this card's state so a requeued card shows its updated
        // previews and loses the "New" chip on its second appearance.
        queue = queue.map((q) =>
          q.problemId === item.problemId && q.card.id === item.card.id
            ? { ...q, state: result.state }
            : q
        );
      }
    } catch {
      saveFailed = true;
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
    if (phase !== 'reviewing') return;

    if (!revealed && (e.key === ' ' || e.key === 'Enter')) {
      e.preventDefault();
      revealed = true;
    } else if (revealed && ['1', '2', '3', '4'].includes(e.key)) {
      e.preventDefault();
      const grades: FlashcardGrade[] = ['again', 'hard', 'good', 'easy'];
      void grade(grades[Number(e.key) - 1]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      phase = 'summary';
      revealed = false;
    }
  }
</script>

<svelte:head><title>Review · Jeff Course</title></svelte:head>
<svelte:window onkeydown={onKeydown} />

<div class="review-shell">
  <Header crumbs={[{ label: 'Review' }]} />

  <main class="review-main">
    {#if phase === 'intro'}
      <header class="review-header">
        <div class="eyebrow">Spaced repetition</div>
        <h1>Daily review</h1>
        <p class="lede">
          Every flashcard deck in every course you are enrolled in, scheduled together.
          Cards you found hard come back sooner; cards you know drift further out.
        </p>
      </header>

      {#if summary.length === 0}
        <section class="empty-card">
          <h2>No decks yet</h2>
          <p>
            Enrol in a course with flashcard modules and its cards will start showing up here.
          </p>
          <a class="cta-primary" href="/tracks">Browse courses</a>
        </section>
      {:else}
        <section class="panel">
          <div class="stats-grid">
            <div>
              <span class="stat-value">{totalDue}</span>
              <span class="stat-label">Due now</span>
            </div>
            <div>
              <span class="stat-value">{totalFresh}</span>
              <span class="stat-label">Never seen</span>
            </div>
            <div>
              <span class="stat-value">{totalLearned} / {totalCards}</span>
              <span class="stat-label">Learned</span>
            </div>
            <div>
              <span class="stat-value">{summary.length}</span>
              <span class="stat-label">Decks</span>
            </div>
          </div>

          <div class="button-row">
            <button class="cta-primary" onclick={() => start(true)} disabled={sessionSize === 0}>
              {sessionSize > 0 ? `Review ${sessionSize} cards` : 'All caught up'}
            </button>
            {#if totalDue > 0 && totalFresh > 0}
              <button class="cta-secondary" onclick={() => start(false)}>
                Due only ({totalDue})
              </button>
            {/if}
          </div>
          <p class="hint">
            <kbd>Space</kbd> flips · <kbd>1</kbd>–<kbd>4</kbd> grade · <kbd>Esc</kbd> ends the session.
            New cards are capped at {newCardAllowance} per sitting so the backlog stays survivable.
          </p>
        </section>

        <section class="deck-table">
          <h2>Decks</h2>
          {#each summary as deck}
            <a class="deck-row" href="/tracks/{deck.trackSlug}/problems/{deck.problemSlug}">
              <div class="deck-names">
                <span class="deck-title">{deck.deckTitle}</span>
                <span class="deck-track">{deck.trackTitle}</span>
              </div>
              <div class="deck-counts">
                {#if deck.due > 0}<span class="count-due">{deck.due} due</span>{/if}
                {#if deck.fresh > 0}<span class="count-new">{deck.fresh} new</span>{/if}
                <span class="count-learned">{deck.learned}/{deck.totalCards} learned</span>
              </div>
            </a>
          {/each}
        </section>
      {/if}
    {:else if phase === 'reviewing' && current}
      <div class="session-bar">
        <span>{index + 1} / {queue.length}</span>
        <span class="session-tallies">
          <span class="tally-again">{tallies.again} again</span>
          <span class="tally-good">{tallies.good + tallies.easy} recalled</span>
        </span>
        <button class="link-button" onclick={() => (phase = 'summary')}>End session <kbd>Esc</kbd></button>
      </div>

      {#key current.card.id}
        <FlashcardStage
          card={current.card}
          {revealed}
          {preview}
          contextLabel={current.deckTitle}
          positionLabel={`Card ${index + 1} of ${queue.length}`}
          isNew={!current.state || current.state.lastReviewedAt === null}
          onReveal={() => (revealed = true)}
          onGrade={grade}
        />
      {/key}

      {#if saveFailed}
        <p class="save-warning">Some reviews could not be saved. Your session keeps going, but progress may not persist.</p>
      {/if}
    {:else}
      <section class="panel results">
        <div class="eyebrow">Session complete</div>
        <h2>{reviewed} reviews</h2>
        <p>{tallies.again} again · {tallies.hard} hard · {tallies.good} good · {tallies.easy} easy</p>
        <div class="button-row">
          <a class="cta-primary" href="/review" data-sveltekit-reload>Reload queue</a>
          <a class="cta-secondary" href="/tracks">Back to courses</a>
        </div>
      </section>
    {/if}
  </main>
</div>

<style>
  .review-shell {
    min-height: 100%;
    background: #0f1117;
    color: #e2e8f0;
    display: flex;
    flex-direction: column;
  }
  .review-main {
    max-width: 900px;
    margin: 0 auto;
    padding: 1.75rem 1.5rem 3rem;
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .eyebrow {
    color: #2dd4bf;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  h1 {
    font-size: 2rem;
    margin: 0.35rem 0;
  }
  h2 {
    font-size: 1.4rem;
    margin: 0.25rem 0 0.6rem;
  }
  .lede {
    color: #94a3b8;
    max-width: 60ch;
  }
  .panel, .empty-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem;
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
  .stat-label, .hint {
    color: #94a3b8;
    font-size: 0.78rem;
  }
  .hint {
    margin: 0.9rem 0 0;
    max-width: 70ch;
  }
  .button-row {
    display: flex;
    gap: 0.65rem;
    flex-wrap: wrap;
    align-items: center;
  }
  .cta-primary, .cta-secondary {
    border-radius: 8px;
    padding: 0.65rem 1rem;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
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
  .cta-secondary:hover {
    border-color: #64748b;
  }
  .cta-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .deck-table {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .deck-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    text-decoration: none;
    color: inherit;
    flex-wrap: wrap;
  }
  .deck-row:hover {
    border-color: #334155;
  }
  .deck-names {
    display: flex;
    flex-direction: column;
  }
  .deck-title {
    font-weight: 700;
  }
  .deck-track {
    color: #64748b;
    font-size: 0.78rem;
  }
  .deck-counts {
    display: flex;
    gap: 0.7rem;
    font-size: 0.78rem;
    color: #94a3b8;
  }
  .count-due { color: #fcd34d; }
  .count-new { color: #93c5fd; }
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
  .results {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: flex-start;
  }
  .save-warning {
    color: #fca5a5;
    font-size: 0.82rem;
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
