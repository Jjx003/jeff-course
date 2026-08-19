<script lang="ts">
  /**
   * FlashcardStage
   *
   * One card: prompt, optional hint, revealed answer, and the four grade
   * buttons. Deliberately stateless about scheduling — it renders whatever
   * interval preview it is handed and reports the grade upward, so the module
   * page and the cross-course /review page can share it.
   */
  import MarkdownRenderer from './MarkdownRenderer.svelte';
  import type { Flashcard, FlashcardGrade } from '$lib/types/course.js';

  interface Props {
    card: Flashcard;
    revealed: boolean;
    /** Deck-relative label, e.g. "Card 4 of 20". */
    positionLabel?: string;
    /** Small badge shown above the prompt, e.g. the deck name on /review. */
    contextLabel?: string;
    /** Per-grade interval preview, e.g. { good: "6d" }. */
    preview?: Partial<Record<FlashcardGrade, string>>;
    /** True the first time this learner sees the card. */
    isNew?: boolean;
    onReveal: () => void;
    onGrade: (grade: FlashcardGrade) => void;
  }

  let {
    card,
    revealed,
    positionLabel = '',
    contextLabel = '',
    preview = {},
    isNew = false,
    onReveal,
    onGrade
  }: Props = $props();

  // Both callers render this inside {#key card.id}, so the component is
  // recreated per card and this resets with it. Doing it in an $effect
  // instead would run after the DOM update, briefly showing the previous
  // card's hint on the new card.
  let hintShown = $state(false);

  const GRADES: { grade: FlashcardGrade; label: string; key: string; tone: string }[] = [
    { grade: 'again', label: 'Again', key: '1', tone: 'grade-again' },
    { grade: 'hard',  label: 'Hard',  key: '2', tone: 'grade-hard'  },
    { grade: 'good',  label: 'Good',  key: '3', tone: 'grade-good'  },
    { grade: 'easy',  label: 'Easy',  key: '4', tone: 'grade-easy'  }
  ];
</script>

<section class="card-stage">
  <div class="card-topbar">
    <span class="card-context">
      {#if contextLabel}<span class="context-chip">{contextLabel}</span>{/if}
      {#if isNew}<span class="new-chip">New</span>{/if}
      {#each card.tags ?? [] as tag}<span class="tag-chip">{tag}</span>{/each}
    </span>
    {#if positionLabel}<span class="card-position">{positionLabel}</span>{/if}
  </div>

  <div class="card-face card-front">
    <MarkdownRenderer content={card.front} variant="study" />
  </div>

  {#if card.hint && !revealed}
    {#if hintShown}
      <div class="card-hint">
        <MarkdownRenderer content={card.hint} variant="compact" />
      </div>
    {:else}
      <button class="ghost-button" onclick={() => (hintShown = true)}>
        Show hint
      </button>
    {/if}
  {/if}

  {#if revealed}
    <div class="card-face card-back">
      <MarkdownRenderer content={card.back} variant="study" />
      {#if card.source}
        <p class="card-source">{card.source}</p>
      {/if}
    </div>

    <div class="grade-row">
      {#each GRADES as g}
        <button class="grade-button {g.tone}" onclick={() => onGrade(g.grade)}>
          <span class="grade-label">{g.label}</span>
          <span class="grade-meta">
            {#if preview[g.grade]}<span class="grade-interval">{preview[g.grade]}</span>{/if}
            <kbd>{g.key}</kbd>
          </span>
        </button>
      {/each}
    </div>
    <p class="stage-hint">
      Grade honestly. <strong>Again</strong> means you could not have said it out loud in an interview.
    </p>
  {:else}
    <button class="reveal-button" onclick={onReveal}>
      Show answer <kbd>Space</kbd>
    </button>
    <p class="stage-hint">Say the answer out loud before you flip. Recognizing it is not recalling it.</p>
  {/if}
</section>

<style>
  .card-stage {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .card-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  .card-context {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    align-items: center;
  }
  .context-chip, .new-chip, .tag-chip {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 0.15rem 0.55rem;
    border: 1px solid #334155;
    color: #94a3b8;
  }
  .context-chip {
    color: #93c5fd;
    border-color: rgba(59, 130, 246, 0.4);
    background: rgba(59, 130, 246, 0.1);
  }
  .new-chip {
    color: #fbbf24;
    border-color: rgba(251, 191, 36, 0.4);
    background: rgba(251, 191, 36, 0.1);
  }
  .card-position {
    color: #64748b;
    font-size: 0.78rem;
  }
  .card-face {
    min-height: 4rem;
  }
  .card-front {
    font-size: 1.15rem;
  }
  .card-back {
    border-top: 1px solid #1e293b;
    padding-top: 1rem;
  }
  .card-source {
    color: #64748b;
    font-size: 0.78rem;
    margin-top: 0.75rem;
  }
  .card-hint {
    border-left: 3px solid #f59e0b;
    background: rgba(245, 158, 11, 0.08);
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
  }
  .reveal-button {
    background: #2563eb;
    border: 1px solid #3b82f6;
    color: white;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-weight: 700;
    cursor: pointer;
  }
  .reveal-button:hover {
    background: #1d4ed8;
  }
  .ghost-button {
    align-self: flex-start;
    background: transparent;
    border: 1px solid #334155;
    color: #cbd5e1;
    border-radius: 8px;
    padding: 0.4rem 0.7rem;
    font-size: 0.82rem;
    cursor: pointer;
  }
  .ghost-button:hover {
    border-color: #475569;
  }
  .grade-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.6rem;
  }
  .grade-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    border-radius: 8px;
    padding: 0.65rem 0.5rem;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid #334155;
    background: #0f1117;
    color: #e2e8f0;
  }
  .grade-button:hover {
    border-color: #64748b;
  }
  .grade-again { border-color: rgba(239, 68, 68, 0.45); color: #fca5a5; }
  .grade-hard  { border-color: rgba(245, 158, 11, 0.45); color: #fcd34d; }
  .grade-good  { border-color: rgba(34, 197, 94, 0.45); color: #86efac; }
  .grade-easy  { border-color: rgba(56, 189, 248, 0.45); color: #7dd3fc; }
  .grade-label {
    font-size: 0.95rem;
  }
  .grade-meta {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.7rem;
    font-weight: 500;
    color: #94a3b8;
  }
  .grade-interval {
    font-variant-numeric: tabular-nums;
  }
  .stage-hint {
    color: #64748b;
    font-size: 0.8rem;
    margin: 0;
  }
  kbd {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.05rem 0.3rem;
    font-size: 0.7rem;
  }
  @media (max-width: 620px) {
    .grade-row {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
