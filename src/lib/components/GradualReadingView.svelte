<script lang="ts">
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import ReadingAudioPlayer from '$lib/components/ReadingAudioPlayer.svelte';
  import type { ReadingAudioClip } from '$lib/types/audio.js';
  import type { ProblemMeta } from '$lib/types/course.js';
  import type { GradualReadStep } from '$lib/reading/gradualReader.js';

  interface Props {
    steps: GradualReadStep[];
    activeIndex: number;
    audioClips?: ReadingAudioClip[];
    trackSlug: string;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
    isComplete: boolean;
    isMarking: boolean;
    onIndexChange: (index: number) => void;
    onMarkComplete: () => void;
    onAudioWordChange?: (clip: ReadingAudioClip, clipIndex: number, wordIndex: number) => void;
  }

  let {
    steps,
    activeIndex,
    audioClips = [],
    trackSlug,
    prevProblem,
    nextProblem,
    isComplete,
    isMarking,
    onIndexChange,
    onMarkComplete,
    onAudioWordChange
  }: Props = $props();

  let currentStep = $derived(steps[activeIndex] ?? steps[0]);
  let stepCount = $derived(steps.length);
  let progressPercent = $derived(stepCount <= 1 ? 100 : ((activeIndex + 1) / stepCount) * 100);
  let isFirst = $derived(activeIndex <= 0);
  let isLast = $derived(activeIndex >= stepCount - 1);

  function goTo(index: number) {
    if (stepCount === 0) return;
    onIndexChange(Math.max(0, Math.min(stepCount - 1, index)));
  }

  function next() {
    goTo(activeIndex + 1);
  }

  function previous() {
    goTo(activeIndex - 1);
  }

  onMount(() => {
    if (!browser) return;
    const onKeydown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest('input, textarea, select, button, a')) return;

      if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') {
        event.preventDefault();
        next();
      } else if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
        event.preventDefault();
        previous();
      } else if (event.key === 'Home') {
        event.preventDefault();
        goTo(0);
      } else if (event.key === 'End') {
        event.preventDefault();
        goTo(stepCount - 1);
      }
    };

    window.addEventListener('keydown', onKeydown);
    return () => window.removeEventListener('keydown', onKeydown);
  });
</script>

{#if currentStep}
  <section class="gradual-reader" aria-label="Focused reading mode">
    <div class="reader-topline">
      <div class="reader-step-meta">
        <span>{currentStep.sectionLabel}</span>
        <span>{activeIndex + 1} / {stepCount}</span>
      </div>
      <div class="reader-progress" aria-hidden="true">
        <div class="reader-progress-fill" style={`width: ${progressPercent}%`}></div>
      </div>
    </div>

    <ReadingAudioPlayer
      clips={audioClips}
      activeIndex={activeIndex}
      syncToActiveIndex={true}
      onWordChange={onAudioWordChange}
      onAdvance={(index) => {
        if (index < stepCount) goTo(index);
      }}
    />

    <article class="reader-card">
      <div class="reader-card-header">
        <p class="reader-kicker">Focus step</p>
        <h2>{currentStep.title}</h2>
      </div>
      <MarkdownRenderer
        content={currentStep.content}
        variant="reading"
        headingPrefix={`focus-${currentStep.id}`}
      />
    </article>

    <div class="reader-actions">
      <button class="reader-nav-button" onclick={previous} disabled={isFirst}>
        <span aria-hidden="true">&larr;</span>
        <span>Back</span>
      </button>

      <div class="reader-dots" aria-label="Reading step picker">
        {#each steps as step, index}
          <button
            class:active={index === activeIndex}
            aria-label={`Go to ${step.sectionLabel} step ${index + 1}`}
            aria-current={index === activeIndex ? 'step' : undefined}
            onclick={() => goTo(index)}
          ></button>
        {/each}
      </div>

      {#if isLast}
        <button
          class="reader-nav-button primary"
          onclick={onMarkComplete}
          disabled={isComplete || isMarking}
        >
          <span>{isComplete ? 'Completed' : isMarking ? 'Marking...' : 'Mark complete'}</span>
        </button>
      {:else}
        <button class="reader-nav-button primary" onclick={next}>
          <span>Next</span>
          <span aria-hidden="true">&rarr;</span>
        </button>
      {/if}
    </div>

    {#if isLast}
      <div class="reader-finish">
        <div>
          <div class="finish-title">{isComplete ? 'Completed' : 'End of focused read'}</div>
          <div class="finish-sub">
            {isComplete
              ? 'This module has been counted toward your progress.'
              : 'Mark it complete when the ideas feel settled enough to move on.'}
          </div>
        </div>
      </div>
    {/if}

    <footer class="reader-footer">
      <ProblemNav {trackSlug} {prevProblem} {nextProblem} />
    </footer>
  </section>
{/if}

<style>
  .gradual-reader {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: min(100%, 880px);
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  .reader-topline {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .reader-step-meta {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .reader-progress {
    height: 6px;
    overflow: hidden;
    border-radius: 999px;
    background: #1e293b;
  }

  .reader-progress-fill {
    height: 100%;
    border-radius: inherit;
    background: #38bdf8;
    transition: width 160ms ease;
  }

  .reader-card {
    min-height: min(58vh, 620px);
    padding: 1.75rem 2rem 2rem;
    border: 1px solid #243044;
    border-radius: 8px;
    background: #111827;
    box-shadow: 0 18px 50px rgba(2, 6, 23, 0.28);
  }

  .reader-card-header {
    padding-bottom: 1rem;
    margin-bottom: 0.25rem;
    border-bottom: 1px solid #1e293b;
  }

  .reader-kicker {
    margin: 0 0 0.4rem;
    color: #67e8f9;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .reader-card h2 {
    margin: 0;
    color: #f8fafc;
    font-size: 1.45rem;
    line-height: 1.25;
    font-weight: 700;
  }

  .reader-actions {
    display: grid;
    grid-template-columns: minmax(108px, auto) 1fr minmax(108px, auto);
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 0;
  }

  .reader-nav-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    min-height: 38px;
    padding: 0.45rem 0.85rem;
    border: 1px solid #334155;
    border-radius: 6px;
    background: #131720;
    color: #cbd5e1;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background 140ms ease, color 140ms ease, border-color 140ms ease;
  }

  .reader-nav-button:hover:not(:disabled) {
    border-color: #475569;
    background: #1e293b;
    color: #f8fafc;
  }

  .reader-nav-button.primary {
    border-color: #0ea5e9;
    background: #0284c7;
    color: #fff;
  }

  .reader-nav-button.primary:hover:not(:disabled) {
    background: #0369a1;
  }

  .reader-nav-button:disabled {
    cursor: not-allowed;
    opacity: 0.48;
  }

  .reader-dots {
    display: flex;
    justify-content: center;
    gap: 0.35rem;
    min-width: 0;
    overflow-x: auto;
    padding: 0.35rem;
  }

  .reader-dots button {
    width: 8px;
    height: 8px;
    flex: 0 0 auto;
    border: 0;
    border-radius: 999px;
    background: #475569;
    transition: background 140ms ease, transform 140ms ease, width 140ms ease;
  }

  .reader-dots button.active {
    width: 22px;
    background: #38bdf8;
  }

  .reader-finish {
    display: flex;
    align-items: center;
    padding: 1rem 1.1rem;
    border: 1px solid #1e293b;
    border-radius: 8px;
    background: #131720;
  }

  .finish-title {
    color: #e2e8f0;
    font-size: 0.95rem;
    font-weight: 700;
  }

  .finish-sub {
    margin-top: 0.2rem;
    color: #94a3b8;
    font-size: 0.82rem;
    line-height: 1.45;
  }

  .reader-footer {
    margin-top: 0.5rem;
    border-top: 1px solid #1e293b;
  }

  @media (max-width: 720px) {
    .gradual-reader {
      padding: 1rem 1rem 3rem;
    }

    .reader-card {
      min-height: auto;
      padding: 1.25rem 1rem 1.5rem;
    }

    .reader-actions {
      grid-template-columns: 1fr 1fr;
    }

    .reader-dots {
      grid-column: 1 / -1;
      grid-row: 2;
    }
  }
</style>
