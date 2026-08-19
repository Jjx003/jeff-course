<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { browser } from '$app/environment';
  import Header from '$lib/components/Header.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import type { DrillConfig, DrillItem, DrillProgress, Problem, ProblemMeta, Track } from '$lib/types/course.js';

  interface Props {
    track: Track;
    problem: Problem;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
    drill: DrillConfig;
    initiallyCompleted?: boolean;
    initialProgress?: DrillProgress | null;
    onPassed?: (correct: number, total: number) => void;
  }

  type Phase = 'intro' | 'running' | 'results';
  type GeneratedPrompt = {
    item: DrillItem;
    prompt: string;
    correct: number;
    explanation: string;
    suffix: string;
  };
  type ResponseRecord = {
    prompt: GeneratedPrompt;
    answer: string;
    correct: boolean;
    responseMs: number;
  };

  let {
    track,
    problem,
    prevProblem,
    nextProblem,
    drill,
    initiallyCompleted = false,
    initialProgress = null,
    onPassed
  }: Props = $props();

  const DEFAULT_SECONDS = 120;
  const DEFAULT_TARGET = 0.8;
  const DEFAULT_ITEMS = 20;

  let phase = $state<Phase>('intro');
  let progress = $state<DrillProgress | null>(null);
  let isComplete = $state(false);
  let prompts = $state<GeneratedPrompt[]>([]);
  let responses = $state<ResponseRecord[]>([]);
  let currentIndex = $state(0);
  let currentAnswer = $state('');
  let answeredCurrent = $state<ResponseRecord | null>(null);
  let itemStartedAt = $state(0);
  let roundStartedAt = $state(0);
  let remainingSeconds = $state(DEFAULT_SECONDS);
  let isRecording = $state(false);
  let lastSeenProblemId = $state('');

  let timer: ReturnType<typeof setInterval> | null = null;

  let problemId = $derived(`${track.slug}/${problem.slug}`);
  let targetAccuracy = $derived(drill.targetAccuracy ?? DEFAULT_TARGET);
  let targetPct = $derived(Math.round(targetAccuracy * 100));
  let roundSeconds = $derived(drill.roundSeconds ?? DEFAULT_SECONDS);
  let itemsPerRound = $derived(drill.itemsPerRound ?? DEFAULT_ITEMS);
  let currentPrompt = $derived(prompts[currentIndex] ?? null);
  let correctCount = $derived(responses.filter((r) => r.correct).length);
  let accuracy = $derived(responses.length === 0 ? 0 : correctCount / responses.length);
  let accuracyPct = $derived(Math.round(accuracy * 100));
  let avgMs = $derived.by(() => {
    if (responses.length === 0) return 0;
    return Math.round(responses.reduce((sum, r) => sum + r.responseMs, 0) / responses.length);
  });
  let bestStreak = $derived.by(() => {
    let best = 0;
    let current = 0;
    for (const r of responses) {
      current = r.correct ? current + 1 : 0;
      best = Math.max(best, current);
    }
    return best;
  });
  let didPass = $derived(responses.length > 0 && accuracy >= targetAccuracy);

  onMount(() => {
    if (!browser) return;
    progress = initialProgress;
    isComplete = initiallyCompleted;
    remainingSeconds = drill.roundSeconds ?? DEFAULT_SECONDS;
    lastSeenProblemId = problemId;
    void refreshProgress();
  });

  $effect(() => {
    const pid = problemId;
    if (!lastSeenProblemId || pid === lastSeenProblemId) return;
    stopTimer();
    lastSeenProblemId = pid;
    phase = 'intro';
    progress = initialProgress;
    isComplete = initiallyCompleted;
    prompts = [];
    responses = [];
    currentIndex = 0;
    currentAnswer = '';
    answeredCurrent = null;
    remainingSeconds = drill.roundSeconds ?? DEFAULT_SECONDS;
    void refreshProgress();
  });

  onDestroy(() => {
    stopTimer();
  });

  async function refreshProgress() {
    try {
      const { drillService, readingProgressService } = await import('$lib/services/index.js');
      const [p, completed] = await Promise.all([
        drillService.getProgress(problemId, targetAccuracy),
        readingProgressService.isCompleted(problemId)
      ]);
      progress = p;
      isComplete = completed;
    } catch {
      // non-fatal
    }
  }

  function randomParam(def: { min: number; max: number; step: number }): number {
    const minSteps = Math.round(def.min / def.step);
    const maxSteps = Math.round(def.max / def.step);
    const n = Math.floor(Math.random() * (maxSteps - minSteps + 1)) + minSteps;
    return n * def.step;
  }

  function evalExpr(expr: string, names: string[], values: number[]): number {
    try {
      // eslint-disable-next-line @typescript-eslint/no-implied-eval
      return Number(new Function(...names, `return (${expr})`)(...values));
    } catch {
      return 0;
    }
  }

  function interpolate(template: string, names: string[], values: number[]): string {
    return template.replace(/\{\{([^}]+)\}\}/g, (_, inner: string) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-implied-eval
        const result = new Function(...names, `return (${inner.trim()})`)(...values);
        return String(result);
      } catch {
        return `{{${inner}}}`;
      }
    });
  }

  /**
   * Absolute slack and percentage slack are combined by taking whichever is
   * larger, so one item can span its whole parameter grid: the absolute value
   * keeps small answers gradeable, the percentage stops the top of the range
   * from demanding four-significant-figure mental arithmetic.
   */
  function effectiveTolerance(item: DrillItem, correct: number): number {
    const absolute = item.tolerance ?? 0;
    const pct = item.tolerancePercent ?? 0;
    if (pct <= 0) return absolute;
    return Math.max(absolute, (Math.abs(correct) * pct) / 100);
  }

  function generatePrompt(): GeneratedPrompt {
    const items = drill.items ?? [];
    const item = items[Math.floor(Math.random() * items.length)] ?? items[0];
    const names = Object.keys(item.params ?? {});
    const values = names.map((name) => randomParam(item.params[name]));
    return {
      item,
      prompt: interpolate(item.prompt_template, names, values),
      correct: evalExpr(item.correct_formula, names, values),
      explanation: interpolate(item.explanation_template ?? '', names, values),
      suffix: item.answer_suffix ?? ''
    };
  }

  function buildRound(): GeneratedPrompt[] {
    return Array.from({ length: itemsPerRound }, () => generatePrompt());
  }

  function startRound() {
    if (!drill.items || drill.items.length === 0) return;
    stopTimer();
    prompts = buildRound();
    responses = [];
    currentIndex = 0;
    currentAnswer = '';
    answeredCurrent = null;
    remainingSeconds = roundSeconds;
    itemStartedAt = Date.now();
    roundStartedAt = itemStartedAt;
    phase = 'running';
    timer = setInterval(() => {
      remainingSeconds = Math.max(0, remainingSeconds - 1);
      if (remainingSeconds === 0) {
        void finishRound();
      }
    }, 1000);
  }

  function stopTimer() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function submitAnswer() {
    if (phase !== 'running' || !currentPrompt || answeredCurrent) return;
    const numeric = Number(currentAnswer.replace(/[,%\s]/g, ''));
    const tolerance = effectiveTolerance(currentPrompt.item, currentPrompt.correct);
    const isCorrect = Number.isFinite(numeric) && Math.abs(numeric - currentPrompt.correct) <= tolerance;
    const record: ResponseRecord = {
      prompt: currentPrompt,
      answer: currentAnswer,
      correct: isCorrect,
      responseMs: Math.max(0, Date.now() - itemStartedAt)
    };
    answeredCurrent = record;
    responses = [...responses, record];
  }

  async function nextPrompt() {
    if (!answeredCurrent) return;
    if (currentIndex >= prompts.length - 1) {
      await finishRound();
      return;
    }
    currentIndex += 1;
    currentAnswer = '';
    answeredCurrent = null;
    itemStartedAt = Date.now();
  }

  async function finishRound() {
    if (phase !== 'running') return;
    stopTimer();
    phase = 'results';
    const durationMs = Math.max(0, Date.now() - roundStartedAt);
    if (!browser) return;
    isRecording = true;
    try {
      const { drillService } = await import('$lib/services/index.js');
      const outcome = await drillService.recordAttempt(problemId, {
        total: responses.length,
        correct: correctCount,
        avgMs,
        bestStreak,
        durationMs,
        targetAccuracy
      });
      if (outcome.wasNewCompletion) {
        isComplete = true;
        onPassed?.(correctCount, responses.length);
      }
      progress = await drillService.getProgress(problemId, targetAccuracy);
    } catch {
      // Results remain useful locally even if persistence fails.
    } finally {
      isRecording = false;
    }
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
    if (phase === 'intro' && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      startRound();
    } else if (phase === 'running' && e.key === 'Enter') {
      e.preventDefault();
      if (answeredCurrent) void nextPrompt();
      else submitAnswer();
    } else if (phase === 'results' && e.key.toLowerCase() === 'r') {
      e.preventDefault();
      startRound();
    }
  }

  function formatMs(ms: number | null | undefined): string {
    if (!ms) return '-';
    return `${(ms / 1000).toFixed(1)}s`;
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="drill-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <main class="drill-main">
    <article class="drill-article">
      <header class="drill-header">
        <div class="drill-eyebrow">Drill · {track.title} · Module {problem.order.toString().padStart(2, '0')}</div>
        <h1>{drill.title ?? problem.title}</h1>
        <div class="drill-meta">
          <span class="badge badge-blue">{itemsPerRound} prompts</span>
          <span class="badge badge-blue">{roundSeconds}s round</span>
          <span class="badge badge-blue">Target {targetPct}%</span>
          {#if isComplete}<span class="badge badge-green">Completed</span>{/if}
        </div>
        {#if problem.description}
          <p>{problem.description}</p>
        {/if}
      </header>

      {#if phase === 'intro'}
        {#if problem.tabs.problem.trim()}
          <section class="drill-copy">
            <MarkdownRenderer content={problem.tabs.problem} variant="study" />
          </section>
        {/if}

        <section class="drill-card">
          <div class="stats-grid">
            <div>
              <span class="stat-value">{progress?.attempts ?? 0}</span>
              <span class="stat-label">Rounds</span>
            </div>
            <div>
              <span class="stat-value">{progress?.bestAccuracy === null || progress?.bestAccuracy === undefined ? '-' : `${Math.round(progress.bestAccuracy * 100)}%`}</span>
              <span class="stat-label">Best accuracy</span>
            </div>
            <div>
              <span class="stat-value">{formatMs(progress?.bestAvgMs)}</span>
              <span class="stat-label">Best avg time</span>
            </div>
            <div>
              <span class="stat-value">{progress?.bestStreak ?? '-'}</span>
              <span class="stat-label">Best streak</span>
            </div>
          </div>
          <button class="cta-primary" onclick={startRound}>Start drill</button>
          <span class="hint">Press <kbd>Enter</kbd> to start. Type numbers only; suffixes are optional.</span>
        </section>
      {:else if phase === 'running' && currentPrompt}
        <section class="play-card">
          <div class="play-topbar">
            <span>Prompt {currentIndex + 1} / {prompts.length}</span>
            <span>{remainingSeconds}s</span>
            <span>{correctCount} / {responses.length} correct</span>
          </div>
          <div class="prompt">
            <MarkdownRenderer content={currentPrompt.prompt} variant="compact" />
          </div>
          <div class="answer-row">
            <input
              bind:value={currentAnswer}
              inputmode="decimal"
              autocomplete="off"
              disabled={answeredCurrent !== null}
              placeholder="Your answer"
            />
            <span class="suffix">{currentPrompt.suffix}</span>
            <button class="cta-primary" onclick={answeredCurrent ? nextPrompt : submitAnswer}>
              {answeredCurrent ? (currentIndex >= prompts.length - 1 ? 'Finish' : 'Next') : 'Check'}
            </button>
          </div>
          {#if answeredCurrent}
            <div class="feedback" class:feedback-ok={answeredCurrent.correct} class:feedback-bad={!answeredCurrent.correct}>
              <strong>{answeredCurrent.correct ? 'Correct' : `Answer: ${currentPrompt.correct}${currentPrompt.suffix}`}</strong>
              {#if currentPrompt.explanation}
                <MarkdownRenderer content={currentPrompt.explanation} variant="compact" />
              {/if}
            </div>
          {/if}
        </section>
      {:else if phase === 'results'}
        <section class="results-card" class:results-pass={didPass}>
          <div>
            <div class="result-kicker">{didPass ? 'Target met' : 'Keep building fluency'}</div>
            <h2>{correctCount} / {responses.length} · {accuracyPct}%</h2>
            <p>
              Average response {formatMs(avgMs)} · best streak {bestStreak}
              {#if isRecording} · saving...{/if}
            </p>
          </div>
          <button class="cta-primary" onclick={startRound}>Run it again <kbd>R</kbd></button>
        </section>

        <section class="review-list">
          {#each responses as r, i}
            <div class="review-row" class:review-ok={r.correct}>
              <span>{i + 1}</span>
              <div>
                <MarkdownRenderer content={r.prompt.prompt} variant="compact" />
                <small>Your answer: {r.answer || '-'} · Correct: {r.prompt.correct}{r.prompt.suffix} · {formatMs(r.responseMs)}</small>
              </div>
            </div>
          {/each}
        </section>
      {/if}

      <ProblemNav {prevProblem} {nextProblem} trackSlug={track.slug} />
    </article>
  </main>
</div>

<style>
  .drill-shell {
    min-height: 100%;
    background: #0f1117;
    color: #e2e8f0;
  }
  .drill-main {
    max-width: 980px;
    margin: 0 auto;
    padding: 1.5rem;
  }
  .drill-article {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .drill-header {
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1rem;
  }
  .drill-eyebrow {
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
  .drill-meta, .play-topbar, .answer-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    flex-wrap: wrap;
  }
  .drill-card, .play-card, .results-card {
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
    font-size: 1.4rem;
    font-weight: 800;
    color: #f8fafc;
  }
  .stat-label, .hint {
    color: #94a3b8;
    font-size: 0.78rem;
  }
  .play-topbar {
    justify-content: space-between;
    color: #94a3b8;
    font-size: 0.82rem;
    margin-bottom: 1rem;
  }
  .prompt {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }
  input {
    min-width: 180px;
    background: #0f1117;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #f8fafc;
    padding: 0.7rem 0.85rem;
    font-size: 1rem;
  }
  input:focus {
    outline: none;
    border-color: #60a5fa;
  }
  .suffix {
    color: #94a3b8;
    min-width: 1.5rem;
  }
  .cta-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: #2563eb;
    border: 1px solid #3b82f6;
    color: white;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    font-weight: 700;
    cursor: pointer;
  }
  .cta-primary:hover {
    background: #1d4ed8;
  }
  .feedback {
    margin-top: 1rem;
    border-left: 3px solid #ef4444;
    background: rgba(239, 68, 68, 0.08);
    border-radius: 8px;
    padding: 0.85rem 1rem;
  }
  .feedback-ok {
    border-left-color: #22c55e;
    background: rgba(34, 197, 94, 0.08);
  }
  .results-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
  .results-pass {
    border-color: rgba(34, 197, 94, 0.35);
  }
  .result-kicker {
    color: #60a5fa;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .results-pass .result-kicker {
    color: #4ade80;
  }
  h2 {
    margin: 0.25rem 0;
    font-size: 2rem;
  }
  .review-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .review-row {
    display: grid;
    grid-template-columns: 2rem 1fr;
    gap: 0.75rem;
    background: #131720;
    border: 1px solid #1e293b;
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 0.75rem;
  }
  .review-ok {
    border-left-color: #22c55e;
  }
  small {
    color: #94a3b8;
  }
  kbd {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.05rem 0.3rem;
    font-size: 0.72rem;
  }
  @media (max-width: 680px) {
    .stats-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .results-card {
      align-items: flex-start;
      flex-direction: column;
    }
  }
</style>
