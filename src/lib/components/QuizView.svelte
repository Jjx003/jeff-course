<script lang="ts">
  /**
   * QuizView — interactive quiz module.
   *
   * Three phases:
   *   intro    → meta header, problem.md briefing, stats (best score, attempts,
   *              question count, est time, pass threshold), big Start CTA.
   *   quiz     → one question at a time with a running score chip, keyboard
   *              shortcuts (1-9 / T-F / Enter / R), and instant explanation
   *              feedback after each answer.
   *   results  → pass/fail header, per-question review (all / missed only),
   *              best-score line, Retake + Next-module CTAs.
   *
   * Completion semantics: a quiz module is considered "complete" the first
   * time the user scores ≥ pass threshold (default 70%). The server records
   * every attempt in `quiz_attempts` and flips `reading_completions` on the
   * first passing attempt — same 5-pt reward + streak credit as readings.
   *
   * Supports `multiple_choice`, `true_false`, and `parametric` question types.
   * Parametric questions re-randomize on every attempt.
   */
  import { onMount, tick } from 'svelte';
  import { browser } from '$app/environment';
  import Header from '$lib/components/Header.svelte';
  import CourseExplorer, { type ExplorerSection } from '$lib/components/CourseExplorer.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import InlineMarkdown from '$lib/components/InlineMarkdown.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import type {
    Problem,
    ProblemMeta,
    Track,
    QuizQuestion,
    QuizProgress,
    ResolvedQuestion
  } from '$lib/types/course.js';

  interface Props {
    track: Track;
    problem: Problem;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
    quizQuestions: QuizQuestion[];
    /** Pre-resolved completion state from SSR; avoids a UI flash on hydration. */
    initiallyCompleted?: boolean;
    /** Pre-resolved quiz progress (best score, attempts) from SSR. */
    initialProgress?: QuizProgress | null;
    /** Called when the user first passes this quiz. */
    onPassed?: (score: number, total: number) => void;
  }

  let {
    track,
    problem,
    prevProblem,
    nextProblem,
    quizQuestions,
    initiallyCompleted = false,
    initialProgress = null,
    onPassed
  }: Props = $props();

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };

  const OPTION_LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];
  const DEFAULT_PASS_THRESHOLD = 0.7;
  let isTest = $derived(problem.type === 'test');
  let assessmentNoun = $derived(isTest ? 'test' : 'quiz');
  let assessmentTitle = $derived(isTest ? 'Test' : 'Quiz');

  // ── resolveQuestions ──────────────────────────────────────────────────
  // Pure function: converts raw QuizQuestion[] (which may include parametric
  // types) into a uniform ResolvedQuestion[] ready for the renderer. Each
  // call generates fresh random values for parametric questions.

  function resolveQuestions(questions: QuizQuestion[]): ResolvedQuestion[] {
    return questions.map((q): ResolvedQuestion => {
      if (q.type === 'multiple_choice') {
        const options = q.options ?? [];
        const correctIndex = typeof q.correct === 'number' ? q.correct : 0;
        return {
          id: q.id,
          type: 'multiple_choice',
          stem: q.stem ?? '',
          options,
          correctIndex,
          explanation: q.explanation ?? ''
        };
      }

      if (q.type === 'true_false') {
        const correctBool = q.correct as boolean;
        return {
          id: q.id,
          type: 'true_false',
          stem: q.stem ?? '',
          options: ['True', 'False'],
          correctIndex: correctBool ? 0 : 1,
          explanation: q.explanation ?? ''
        };
      }

      // parametric — generate fresh values, evaluate formulas, shuffle.
      const paramDefs = q.params ?? {};
      const paramNames = Object.keys(paramDefs);
      const paramValues: number[] = paramNames.map((name) => {
        const { min, max, step } = paramDefs[name];
        const minSteps = Math.round(min / step);
        const maxSteps = Math.round(max / step);
        const n = Math.floor(Math.random() * (maxSteps - minSteps + 1)) + minSteps;
        return n * step;
      });

      function evalExpr(expr: string): number {
        try {
          // eslint-disable-next-line @typescript-eslint/no-implied-eval
          return new Function(...paramNames, `return (${expr})`)(...paramValues) as number;
        } catch {
          return 0;
        }
      }

      function interpolate(template: string): string {
        return template.replace(/\{\{([^}]+)\}\}/g, (_, inner: string) => {
          try {
            // eslint-disable-next-line @typescript-eslint/no-implied-eval
            const result = new Function(...paramNames, `return (${inner.trim()})`)(...paramValues);
            return String(result);
          } catch {
            return `{{${inner}}}`;
          }
        });
      }

      const correctValue = evalExpr(q.correct_formula ?? '0');
      const suffix = q.answer_suffix ?? '';

      const distractorValues = (q.distractor_formulas ?? []).map((f) => {
        const val = evalExpr(f);
        return val === correctValue ? correctValue + 1 : val;
      });

      const items: Array<{ label: string; isCorrect: boolean }> = [
        { label: `${correctValue}${suffix}`, isCorrect: true },
        ...distractorValues.map((v) => ({ label: `${v}${suffix}`, isCorrect: false }))
      ];
      for (let i = items.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [items[i], items[j]] = [items[j], items[i]];
      }

      return {
        id: q.id,
        type: 'multiple_choice',
        stem: interpolate(q.stem_template ?? ''),
        options: items.map((it) => it.label),
        correctIndex: items.findIndex((it) => it.isCorrect),
        explanation: interpolate(q.explanation_template ?? '')
      };
    });
  }

  // ── Quiz state ────────────────────────────────────────────────────────
  type Phase = 'intro' | 'quiz' | 'results';

  let phase = $state<Phase>('intro');
  let resolved = $state<ResolvedQuestion[]>([]);
  let currentIndex = $state(0);
  /** Index into resolved[i].options[] chosen per question; null = unanswered. */
  let answers = $state<(number | null)[]>([]);
  /** Wall-clock ms when the current attempt entered the 'quiz' phase. */
  let attemptStartedAt = $state<number | null>(null);
  /** Results filter — show all or only the missed ones. */
  let reviewFilter = $state<'all' | 'missed'>('all');
  /** Per-question expand state on the results screen. */
  let expanded = $state<Record<number, boolean>>({});

  let currentQuestion = $derived(resolved[currentIndex] ?? null);
  let currentAnswer   = $derived(answers[currentIndex] ?? null);
  let isAnswered      = $derived(currentAnswer !== null);
  let isLastQuestion  = $derived(currentIndex === resolved.length - 1);

  let correctCount = $derived(
    isTest && phase !== 'results'
      ? 0
      : answers.reduce<number>((acc, ans, i) => {
          const q = resolved[i];
          if (!q || ans === null) return acc;
          return acc + (ans === q.correctIndex ? 1 : 0);
        }, 0)
  );
  let wrongCount = $derived(
    isTest && phase !== 'results'
      ? 0
      : answers.reduce<number>((acc, ans, i) => {
          const q = resolved[i];
          if (!q || ans === null) return acc;
          return acc + (ans === q.correctIndex ? 0 : 1);
        }, 0)
  );

  let scoreRatio = $derived(resolved.length > 0 ? correctCount / resolved.length : 0);
  let scorePct = $derived(Math.round(scoreRatio * 100));

  let passThreshold = $derived(initialProgress?.passThreshold ?? DEFAULT_PASS_THRESHOLD);
  let passThresholdPct = $derived(Math.round(passThreshold * 100));
  let didPassThisAttempt = $derived(scoreRatio >= passThreshold);

  function isCorrectAnswer(q: ResolvedQuestion, ans: number): boolean {
    return ans === q.correctIndex;
  }

  function questionTypeLabel(q: ResolvedQuestion, raw: QuizQuestion): string {
    if (raw.type === 'parametric') return 'Calculation';
    if (q.type === 'true_false') return 'True / False';
    return 'Multiple choice';
  }

  // ── Progress + completion state ──────────────────────────────────────
  let problemId = $derived(`${track.slug}/${problem.slug}`);
  let isComplete = $state(false);
  let lastSeenProblemId = $state<string | null>(null);
  let progress = $state<QuizProgress | null>(null);
  let isRecording = $state(false);
  let recentOutcome = $state<{
    passed: boolean;
    wasNewCompletion: boolean;
    bestScore: number;
    bestTotal: number;
    attempts: number;
  } | null>(null);

  onMount(() => {
    isComplete = initiallyCompleted;
    progress = initialProgress;
    lastSeenProblemId = problemId;
    resolved = resolveQuestions(quizQuestions);
    answers = resolved.map(() => null as null);
    // Always refresh from API on mount so retakes between problems show
    // accurate best-score info even when SSR was cached.
    tick().then(updateExplorerHeadingFromScroll);
    void refreshProgress(problemId);
  });

  // Reset state when navigating between modules without a remount.
  $effect(() => {
    const pid = problemId;
    if (pid === lastSeenProblemId) return;
    lastSeenProblemId = pid;
    isComplete = false;
    phase = 'intro';
    activeExplorerHeadingId = '';
    currentIndex = 0;
    attemptStartedAt = null;
    recentOutcome = null;
    expanded = {};
    reviewFilter = 'all';
    resolved = resolveQuestions(quizQuestions);
    answers = resolved.map(() => null as null);
    void refreshProgress(pid);
  });

  async function refreshProgress(pid: string) {
    if (!browser) return;
    try {
      const { quizService, readingProgressService } = await import('$lib/services/index.js');
      const [p, completed] = await Promise.all([
        quizService.getProgress(pid),
        readingProgressService.isCompleted(pid)
      ]);
      progress = p;
      isComplete = completed;
    } catch {
      // non-fatal
    }
  }

  // ── Phase transitions ────────────────────────────────────────────────
  function startAttempt() {
    if (quizQuestions.length === 0) return;
    resolved = resolveQuestions(quizQuestions);
    answers = resolved.map(() => null as null);
    currentIndex = 0;
    expanded = {};
    reviewFilter = 'all';
    recentOutcome = null;
    attemptStartedAt = Date.now();
    phase = 'quiz';
  }

  function selectAnswer(idx: number) {
    if (phase !== 'quiz') return;
    if (currentQuestion === null) return;
    if (idx < 0 || idx >= currentQuestion.options.length) return;
    if (isAnswered) return;
    answers[currentIndex] = idx;
  }

  async function nextQuestion() {
    if (phase !== 'quiz' || !isAnswered) return;
    if (isLastQuestion) {
      await finishAttempt();
    } else {
      currentIndex += 1;
    }
  }

  async function finishAttempt() {
    phase = 'results';
    const endedAt = Date.now();
    const durationMs = attemptStartedAt !== null ? endedAt - attemptStartedAt : 0;
    if (!browser) return;
    isRecording = true;
    try {
      const { quizService } = await import('$lib/services/index.js');
      const outcome = await quizService.recordAttempt(problemId, {
        total: resolved.length,
        correct: correctCount,
        durationMs
      });
      recentOutcome = outcome;
      if (outcome.wasNewCompletion) {
        isComplete = true;
        onPassed?.(correctCount, resolved.length);
      }
      // Refresh aggregate progress so the intro/results best-score line is current.
      progress = await quizService.getProgress(problemId);
    } catch {
      // non-fatal; the results screen still works locally.
    } finally {
      isRecording = false;
    }
  }

  function backToIntro() {
    phase = 'intro';
  }

  function toggleExpanded(i: number) {
    expanded[i] = !expanded[i];
  }

  // ── Keyboard shortcuts ───────────────────────────────────────────────
  function onKeyDown(e: KeyboardEvent) {
    if (e.defaultPrevented) return;
    if (e.altKey || e.metaKey || e.ctrlKey) return;
    const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase() ?? '';
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if (phase === 'intro') {
      if (e.key === 'Enter' || e.key === ' ' || e.key.toLowerCase() === 'r') {
        e.preventDefault();
        startAttempt();
      }
      return;
    }

    if (phase === 'quiz') {
      if (!isAnswered) {
        const q = currentQuestion;
        if (!q) return;
        if (q.type === 'true_false') {
          const k = e.key.toLowerCase();
          if (k === 't' || k === '1') {
            e.preventDefault();
            selectAnswer(0);
          } else if (k === 'f' || k === '2') {
            e.preventDefault();
            selectAnswer(1);
          }
          return;
        }
        if (/^[1-9]$/.test(e.key)) {
          const idx = parseInt(e.key, 10) - 1;
          if (idx < q.options.length) {
            e.preventDefault();
            selectAnswer(idx);
          }
          return;
        }
      } else {
        if (e.key === 'Enter' || e.key.toLowerCase() === 'n') {
          e.preventDefault();
          void nextQuestion();
        }
      }
      return;
    }

    if (phase === 'results') {
      if (e.key.toLowerCase() === 'r') {
        e.preventDefault();
        startAttempt();
      }
    }
  }

  // Keyboard shortcuts are wired via <svelte:window onkeydown={...} /> below.

  // ── Derived display helpers ──────────────────────────────────────────
  let bestLine = $derived.by(() => {
    if (!progress || progress.bestScore === null || progress.bestTotal === null) return null;
    const pct = Math.round((progress.bestScore / Math.max(1, progress.bestTotal)) * 100);
    return {
      score: progress.bestScore,
      total: progress.bestTotal,
      pct,
      passed: progress.hasPassed
    };
  });

  let visibleReviewIndices = $derived.by(() => {
    const indices: number[] = [];
    for (let i = 0; i < resolved.length; i++) {
      const q = resolved[i];
      const ans = answers[i];
      if (!q) continue;
      const correct = ans !== null && ans === q.correctIndex;
      if (reviewFilter === 'missed' && correct) continue;
      indices.push(i);
    }
    return indices;
  });

  let quizMain = $state<HTMLElement | undefined>(undefined);
  let explorerOpen = $state(true);
  let activeExplorerSection = $state('problem');
  let activeExplorerHeadingId = $state('');
  let explorerSections = $derived.by<ExplorerSection[]>(() => [
    { id: 'problem', label: 'Briefing', content: problem.tabs.problem }
  ]);

  async function scrollToExplorerTarget(sectionId: string, headingId?: string) {
    activeExplorerSection = sectionId;
    activeExplorerHeadingId = headingId ?? '';
    if (sectionId === 'problem' && phase !== 'intro') {
      phase = 'intro';
    }
    await tick();
    const selector = headingId
      ? `[data-markdown-heading-id="${headingId}"]`
      : `[data-explorer-section="${sectionId}"]`;
    scrollWithin(quizMain, quizMain?.querySelector<HTMLElement>(selector));
  }

  function scrollWithin(container: HTMLElement | undefined, target: HTMLElement | null | undefined) {
    if (!container || !target) return;
    const containerRect = container.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const rawTop = targetRect.top - containerRect.top + container.scrollTop - 12;
    const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
    container.scrollTo({
      top: Math.min(Math.max(0, rawTop), maxTop),
      behavior: 'smooth',
    });
  }

  function updateExplorerHeadingFromScroll() {
    if (!quizMain) return;
    const containerTop = quizMain.getBoundingClientRect().top;
    const threshold = containerTop + 72;
    const headings = Array.from(
      quizMain.querySelectorAll<HTMLElement>('[data-markdown-heading-id]')
    );
    let activeHeading = '';

    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= threshold) {
        activeHeading = heading.dataset.markdownHeadingId ?? '';
      } else {
        break;
      }
    }

    activeExplorerSection = 'problem';
    activeExplorerHeadingId = activeHeading;
  }
</script>

<svelte:window onkeydown={onKeyDown} />

<div class="quiz-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <main class="quiz-main" bind:this={quizMain} onscroll={updateExplorerHeadingFromScroll}>
    <div class="quiz-layout">
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

      <article class="quiz-article">
      <!-- Meta header — present in every phase so the user always knows where they are. -->
      <header class="quiz-header" data-explorer-section="problem">
        <div class="quiz-eyebrow">
          <span class="quiz-eyebrow-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M9.5 9.5a2.5 2.5 0 1 1 4 2c-.8.7-1.5 1.3-1.5 2.5" />
              <circle cx="12" cy="17" r="0.6" fill="currentColor" />
            </svg>
          </span>
          <span>
            Quiz · {track.title} · Module {problem.order.toString().padStart(2, '0')}
          </span>
        </div>
        <h1 class="quiz-title">{problem.title}</h1>
        <div class="quiz-meta">
          <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
            {problem.difficulty}
          </span>
          <span class="text-xs text-slate-500">{problem.estimatedMinutes} min</span>
          <span class="badge badge-blue">{quizQuestions.length} questions</span>
          <span class="badge badge-blue">Pass {passThresholdPct}%</span>
          {#if isComplete}
            <span class="badge badge-green badge-icon">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 13l4 4L19 7" />
              </svg>
              Completed
            </span>
          {/if}
          {#each problem.tags as tag}
            <span class="badge badge-blue">{tag}</span>
          {/each}
        </div>
        {#if problem.description}
          <p class="quiz-description">{problem.description}</p>
        {/if}
      </header>

      <!-- ── Phase: empty (no questions configured) ──────────────────── -->
      {#if quizQuestions.length === 0}
        <div class="quiz-empty">
          <p>No questions found for this {assessmentNoun}. Check that <code>quiz.yaml</code> exists and is valid.</p>
        </div>

      <!-- ── Phase: intro ───────────────────────────────────────────── -->
      {:else if phase === 'intro'}
        {#if problem.tabs.problem.trim()}
          <section class="quiz-intro-body">
            <MarkdownRenderer content={problem.tabs.problem} variant="study" headingPrefix="problem" />
          </section>
        {/if}

        <section class="intro-card" class:intro-card-passed={isComplete}>
          <!-- Stats grid -->
          <div class="intro-stats">
            <div class="intro-stat">
              <div class="intro-stat-value">{quizQuestions.length}</div>
              <div class="intro-stat-label">Questions</div>
            </div>
            <div class="intro-stat">
              <div class="intro-stat-value">~{problem.estimatedMinutes}<span class="intro-stat-unit">m</span></div>
              <div class="intro-stat-label">Est. time</div>
            </div>
            <div class="intro-stat">
              <div class="intro-stat-value">{passThresholdPct}<span class="intro-stat-unit">%</span></div>
              <div class="intro-stat-label">To pass</div>
            </div>
            {#if bestLine}
              <div class="intro-stat intro-stat-best" class:intro-stat-best-passed={bestLine.passed}>
                <div class="intro-stat-value">
                  {bestLine.score}<span class="intro-stat-unit">/{bestLine.total}</span>
                </div>
                <div class="intro-stat-label">Best · {bestLine.pct}%</div>
              </div>
            {:else}
              <div class="intro-stat">
                <div class="intro-stat-value intro-stat-muted">—</div>
                <div class="intro-stat-label">No attempts yet</div>
              </div>
            {/if}
          </div>

          <!-- CTA row -->
          <div class="intro-cta-row">
            <button class="cta-primary" onclick={startAttempt}>
              <span aria-hidden="true">▶</span>
              {progress && progress.attempts > 0 ? `Retake ${assessmentNoun}` : `Start ${assessmentNoun}`}
            </button>
            {#if progress && progress.attempts > 0}
              <span class="intro-cta-sub">
                {progress.attempts} {progress.attempts === 1 ? 'attempt' : 'attempts'}
                {#if isComplete}· passed{/if}
              </span>
            {/if}
            <span class="kbd-hint">Tip: press <kbd>Enter</kbd> to start</span>
          </div>
        </section>

      <!-- ── Phase: quiz ─────────────────────────────────────────────── -->
      {:else if phase === 'quiz' && currentQuestion !== null}
        <!-- Top bar: progress + live score -->
        <div class="quiz-topbar">
          <div class="quiz-progress-row">
            <span class="quiz-progress-label">Question {currentIndex + 1} of {resolved.length}</span>
            <div class="quiz-progress-bar-track" aria-hidden="true">
              <div
                class="quiz-progress-bar-fill"
                style="width: {((currentIndex + (isAnswered ? 1 : 0)) / resolved.length) * 100}%"
              ></div>
            </div>
          </div>

          {#if isTest}
            <div class="score-chip" title="Answers recorded so far">
              <span>{answers.filter((ans) => ans !== null).length} answered</span>
            </div>
          {:else}
          <div class="score-chip" title="Correct / wrong so far">
            <span class="score-chip-correct">
              <span class="dot dot-green" aria-hidden="true"></span>
              {correctCount}
            </span>
            <span class="score-chip-sep">·</span>
            <span class="score-chip-wrong">
              <span class="dot dot-red" aria-hidden="true"></span>
              {wrongCount}
            </span>
          </div>
          {/if}
        </div>

        <!-- Question card -->
        <div class="question-card">
          <div class="question-type-row">
            <span class="qtype-pill">
              {questionTypeLabel(currentQuestion, quizQuestions[currentIndex])}
            </span>
            <button class="exit-link" onclick={backToIntro} title="Exit to quiz intro">
              ← Exit
            </button>
          </div>

          <div class="question-stem">
            <MarkdownRenderer content={currentQuestion.stem} variant="compact" />
          </div>

          {#if currentQuestion.type === 'multiple_choice'}
            <div class="options-list">
              {#each currentQuestion.options as option, i}
                {@const chosen = currentAnswer === i}
                {@const revealAnswer = isAnswered && !isTest}
                {@const correct = revealAnswer && i === currentQuestion.correctIndex}
                {@const wrong = revealAnswer && chosen && !correct}
                <button
                  class="option-btn"
                  class:option-correct={correct}
                  class:option-wrong={wrong}
                  class:option-selected={isAnswered && isTest && chosen}
                  class:option-faded={revealAnswer && !correct && !wrong}
                  class:option-idle={!isAnswered}
                  disabled={isAnswered}
                  onclick={() => selectAnswer(i)}
                >
                  <span class="option-label">{OPTION_LABELS[i] ?? i + 1}</span>
                  <span class="option-text"><InlineMarkdown content={option} /></span>
                  {#if isAnswered && correct}
                    <span class="option-mark option-mark-ok" aria-hidden="true">✓</span>
                  {:else if isAnswered && wrong}
                    <span class="option-mark option-mark-bad" aria-hidden="true">✗</span>
                  {/if}
                </button>
              {/each}
            </div>

          {:else if currentQuestion.type === 'true_false'}
            <div class="tf-row">
              {#each currentQuestion.options as opt, i}
                {@const chosen = currentAnswer === i}
                {@const revealAnswer = isAnswered && !isTest}
                {@const correct = revealAnswer && i === currentQuestion.correctIndex}
                {@const wrong = revealAnswer && chosen && !correct}
                <button
                  class="tf-btn"
                  class:option-correct={correct}
                  class:option-wrong={wrong}
                  class:option-selected={isAnswered && isTest && chosen}
                  class:option-faded={revealAnswer && !correct && !wrong}
                  class:option-idle={!isAnswered}
                  disabled={isAnswered}
                  onclick={() => selectAnswer(i)}
                >
                  <span class="tf-shortcut">{i === 0 ? 'T' : 'F'}</span>
                  <span class="tf-text">{opt}</span>
                  {#if isAnswered && correct}
                    <span class="option-mark option-mark-ok" aria-hidden="true">✓</span>
                  {:else if isAnswered && wrong}
                    <span class="option-mark option-mark-bad" aria-hidden="true">✗</span>
                  {/if}
                </button>
              {/each}
            </div>
          {/if}

          {#if isAnswered && !isTest}
            {@const answered = currentAnswer as number}
            {@const correct = isCorrectAnswer(currentQuestion, answered)}
            <div
              class="explanation-box"
              class:explanation-correct={correct}
              class:explanation-wrong={!correct}
            >
              <div class="explanation-label">
                {correct ? 'Correct!' : 'Not quite.'}
              </div>
              <div class="explanation-body">
                <MarkdownRenderer content={currentQuestion.explanation} variant="compact" />
              </div>
            </div>

            <div class="question-actions">
              <span class="kbd-hint kbd-hint-inline">
                <kbd>Enter</kbd> {isLastQuestion ? 'to see results' : 'for next'}
              </span>
              <button class="cta-primary" onclick={nextQuestion}>
                {isLastQuestion ? 'See results' : 'Next question →'}
              </button>
            </div>
          {:else if !isAnswered}
            <div class="kbd-hint kbd-hint-strip">
              {#if currentQuestion.type === 'true_false'}
                <span><kbd>T</kbd>/<kbd>F</kbd> or <kbd>1</kbd>/<kbd>2</kbd> to answer</span>
              {:else}
                <span>Press <kbd>1</kbd>–<kbd>{Math.min(currentQuestion.options.length, 9)}</kbd> to answer</span>
              {/if}
            </div>
          {:else}
            <div class="question-actions">
              <span class="kbd-hint kbd-hint-inline">
                Answer recorded. <kbd>Enter</kbd> {isLastQuestion ? 'to see results' : 'for next'}
              </span>
              <button class="cta-primary" onclick={nextQuestion}>
                {isLastQuestion ? 'See results' : 'Next question ->'}
              </button>
            </div>
          {/if}
        </div>

      <!-- ── Phase: results ─────────────────────────────────────────── -->
      {:else if phase === 'results'}
        {@const passed = didPassThisAttempt}
        <section class="results-hero" class:results-hero-pass={passed} class:results-hero-fail={!passed}>
          <div class="results-hero-icon" aria-hidden="true">
            {#if passed}
              <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9.5" />
                <path d="M8 12.5l3 3 5-6" />
              </svg>
            {:else}
              <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9.5" />
                <path d="M12 8v5" />
                <circle cx="12" cy="16" r="0.6" fill="currentColor" />
              </svg>
            {/if}
          </div>
          <div class="results-hero-body">
            <div class="results-hero-eyebrow">{passed ? `${assessmentTitle} passed` : 'Almost there'}</div>
            <div class="results-hero-score">
              <span class="results-hero-num">{correctCount}</span>
              <span class="results-hero-divider">/ {resolved.length}</span>
              <span class="results-hero-pct">{scorePct}%</span>
            </div>
            <div class="results-hero-sub">
              {#if passed}
                {#if recentOutcome?.wasNewCompletion}
                  Marked complete · +5 points · added to your streak.
                {:else}
                  You cleared the {passThresholdPct}% threshold.
                {/if}
              {:else}
                Need {passThresholdPct}% to pass — retake to mark this module complete.
              {/if}
            </div>
          </div>
          <div class="results-hero-side">
            <div class="results-bar-track" aria-hidden="true">
              <div class="results-bar-fill" style="width: {scorePct}%"></div>
              <div class="results-bar-threshold" style="left: {passThresholdPct}%" title="Pass threshold"></div>
            </div>
            {#if bestLine}
              <div class="results-best">Best: {bestLine.score}/{bestLine.total} · {bestLine.pct}%</div>
            {/if}
          </div>
        </section>

        <!-- Action row -->
        <section class="results-actions-row">
          <button class="cta-primary" onclick={startAttempt}>
            <span aria-hidden="true">↻</span> Retake
            <span class="kbd-inline"><kbd>R</kbd></span>
          </button>
          {#if passed && nextProblem}
            <a class="cta-secondary" href="/tracks/{track.slug}/problems/{nextProblem.slug}">
              Next module →
            </a>
          {:else if !passed}
            <span class="results-nudge">
              {#if isRecording}Saving attempt…{:else}Review the questions below, then try again.{/if}
            </span>
          {/if}
        </section>

        <!-- Per-question review -->
        <section class="review-section">
          <div class="review-header">
            <h2 class="review-title">Review</h2>
            <div class="review-filter" role="group" aria-label="Filter reviewed questions">
              <button
                class="review-filter-btn"
                class:review-filter-active={reviewFilter === 'all'}
                onclick={() => (reviewFilter = 'all')}
              >
                All <span class="review-filter-count">{resolved.length}</span>
              </button>
              <button
                class="review-filter-btn"
                class:review-filter-active={reviewFilter === 'missed'}
                onclick={() => (reviewFilter = 'missed')}
                disabled={wrongCount === 0}
              >
                Missed <span class="review-filter-count">{wrongCount}</span>
              </button>
            </div>
          </div>

          {#if visibleReviewIndices.length === 0}
            <div class="review-empty">
              {#if reviewFilter === 'missed' && wrongCount === 0}
                Perfect score — nothing to review.
              {:else}
                Nothing to show.
              {/if}
            </div>
          {/if}

          {#each visibleReviewIndices as i}
            {@const q = resolved[i]}
            {@const ans = answers[i]}
            {@const correct = ans !== null && ans === q.correctIndex}
            {@const isOpen = expanded[i] === true}
            <div class="review-card" class:review-card-correct={correct} class:review-card-wrong={!correct}>
              <button
                class="review-summary"
                onclick={() => toggleExpanded(i)}
                aria-expanded={isOpen}
              >
                <span class="review-num">{i + 1}</span>
                <span class="review-status-pill" class:review-status-ok={correct} class:review-status-bad={!correct}>
                  {#if correct}
                    <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M5 13l4 4L19 7" />
                    </svg>
                    Correct
                  {:else}
                    <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M6 6l12 12M18 6L6 18" />
                    </svg>
                    Wrong
                  {/if}
                </span>
                <span class="review-stem-clip">
                  <InlineMarkdown content={q.stem.slice(0, 140) + (q.stem.length > 140 ? '…' : '')} />
                </span>
                <span class="review-chevron" aria-hidden="true">{isOpen ? '▴' : '▾'}</span>
              </button>

              {#if isOpen}
                <div class="review-body">
                  <div class="review-stem">
                    <MarkdownRenderer content={q.stem} variant="compact" />
                  </div>

                  <div class="review-answers">
                    <div class="review-answer review-answer-correct">
                      <div class="review-answer-label">Correct answer</div>
                      <div class="review-answer-text">
                        <InlineMarkdown content={q.options[q.correctIndex] ?? ''} />
                      </div>
                    </div>
                    {#if !correct}
                      <div class="review-answer review-answer-wrong">
                        <div class="review-answer-label">Your answer</div>
                        <div class="review-answer-text">
                          {#if ans === null}
                            <em class="review-answer-blank">Not answered</em>
                          {:else}
                            <InlineMarkdown content={q.options[ans] ?? ''} />
                          {/if}
                        </div>
                      </div>
                    {/if}
                  </div>

                  {#if q.explanation.trim()}
                    <div class="review-explanation">
                      <div class="review-explanation-label">Explanation</div>
                      <MarkdownRenderer content={q.explanation} variant="compact" />
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/each}
        </section>
      {/if}

      <!-- Footer navigation -->
      <footer class="quiz-footer">
        <ProblemNav
          trackSlug={track.slug}
          {prevProblem}
          {nextProblem}
        />
      </footer>
      </article>
    </div>
  </main>
</div>

<style>
  .quiz-shell {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
    overflow: hidden;
    overscroll-behavior: none;
    background: #0f1117;
  }

  .quiz-main {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
  }

  .quiz-layout {
    min-height: 100%;
    display: flex;
    align-items: flex-start;
  }

  .quiz-layout :global(.course-explorer) {
    position: sticky;
    top: 0;
    height: calc(100vh - 56px);
  }

  .quiz-article {
    width: min(100%, 760px);
    max-width: 760px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  /* ── Header ── */
  .quiz-header {
    padding-bottom: 1.5rem;
    margin-bottom: 1.25rem;
    border-bottom: 1px solid #1e293b;
  }

  .quiz-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.7rem;
    font-weight: 600;
    color: #818cf8;
    margin-bottom: 0.75rem;
    padding: 0.2rem 0.55rem 0.2rem 0.4rem;
    background: rgba(129, 140, 248, 0.1);
    border: 1px solid rgba(129, 140, 248, 0.25);
    border-radius: 999px;
  }
  .quiz-eyebrow-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #a5b4fc;
  }

  .quiz-title {
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 1rem;
    letter-spacing: -0.01em;
  }

  .quiz-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  .badge-icon {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }

  .quiz-description {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.6;
    margin: 0;
  }

  /* ── Empty state ── */
  .quiz-empty {
    padding: 2rem;
    color: #64748b;
    font-size: 0.9rem;
    text-align: center;
    background: #131720;
    border: 1px dashed #1e293b;
    border-radius: 10px;
  }

  /* ── Intro phase ── */
  .quiz-intro-body {
    margin-bottom: 1.5rem;
  }

  .intro-card {
    background: linear-gradient(180deg, rgba(129, 140, 248, 0.06), #131720 60%);
    border: 1px solid rgba(129, 140, 248, 0.18);
    border-radius: 14px;
    padding: 1.5rem 1.5rem 1.25rem;
    margin-bottom: 1.5rem;
  }
  .intro-card.intro-card-passed {
    border-color: rgba(34, 197, 94, 0.28);
    background: linear-gradient(180deg, rgba(34, 197, 94, 0.06), #131720 60%);
  }

  .intro-stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.25rem;
  }
  @media (max-width: 540px) {
    .intro-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }

  .intro-stat {
    background: rgba(15, 17, 23, 0.6);
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0.85rem 0.85rem;
    text-align: center;
  }
  .intro-stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }
  .intro-stat-muted {
    color: #475569;
  }
  .intro-stat-unit {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    margin-left: 0.1rem;
  }
  .intro-stat-label {
    font-size: 0.7rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
  }
  .intro-stat-best {
    border-color: rgba(96, 165, 250, 0.3);
    background: rgba(96, 165, 250, 0.06);
  }
  .intro-stat-best .intro-stat-value { color: #93c5fd; }
  .intro-stat-best-passed {
    border-color: rgba(34, 197, 94, 0.4);
    background: rgba(34, 197, 94, 0.07);
  }
  .intro-stat-best-passed .intro-stat-value { color: #86efac; }

  .intro-cta-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    flex-wrap: wrap;
  }

  .intro-cta-sub {
    color: #64748b;
    font-size: 0.8rem;
    font-variant-numeric: tabular-nums;
  }

  /* ── CTAs ── */
  .cta-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(180deg, #6366f1, #4f46e5);
    color: #fff;
    border: 1px solid rgba(99, 102, 241, 0.4);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08) inset, 0 6px 16px rgba(79, 70, 229, 0.25);
    padding: 0.6rem 1.1rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    transition: transform 80ms ease, box-shadow 120ms ease, background 120ms ease;
  }
  .cta-primary:hover {
    background: linear-gradient(180deg, #7077f3, #5b54ea);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.1) inset, 0 8px 20px rgba(79, 70, 229, 0.32);
  }
  .cta-primary:active { transform: translateY(1px); }

  .cta-secondary {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #131720;
    color: #e2e8f0;
    border: 1px solid #334155;
    padding: 0.55rem 0.95rem;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.88rem;
    text-decoration: none;
    transition: border-color 120ms ease, background 120ms ease;
  }
  .cta-secondary:hover {
    border-color: #60a5fa;
    background: #1a1f2e;
  }

  /* ── Quiz phase topbar ── */
  .quiz-topbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }
  .quiz-progress-row {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .quiz-progress-label {
    font-size: 0.75rem;
    color: #94a3b8;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
  .quiz-progress-bar-track {
    flex: 1;
    height: 5px;
    background: #1e293b;
    border-radius: 999px;
    overflow: hidden;
  }
  .quiz-progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #818cf8, #60a5fa);
    border-radius: 999px;
    transition: width 280ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .score-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    font-size: 0.78rem;
    color: #cbd5e1;
    font-variant-numeric: tabular-nums;
  }
  .score-chip-correct, .score-chip-wrong {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }
  .score-chip-sep { color: #475569; }
  .dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 999px;
  }
  .dot-green { background: #22c55e; }
  .dot-red { background: #ef4444; }

  /* ── Question card ── */
  .question-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .question-type-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }
  .qtype-pill {
    display: inline-flex;
    align-items: center;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #818cf8;
    background: rgba(129, 140, 248, 0.1);
    border: 1px solid rgba(129, 140, 248, 0.25);
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
  }
  .exit-link {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 0.75rem;
    cursor: pointer;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
  }
  .exit-link:hover {
    color: #cbd5e1;
    background: #1e293b;
  }

  .question-stem {
    color: #e2e8f0;
    font-size: 1.05rem;
    line-height: 1.65;
    margin-bottom: 1.5rem;
  }
  .question-stem :global(.prose) {
    padding: 0;
  }

  /* ── MC options ── */
  .options-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }

  .option-btn {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    text-align: left;
    padding: 0.85rem 1rem;
    border: 1px solid #334155;
    border-radius: 10px;
    background: #0f1117;
    color: #cbd5e1;
    font-size: 0.95rem;
    cursor: pointer;
    transition: border-color 120ms ease, background 120ms ease,
                color 120ms ease, transform 120ms ease;
  }
  .option-btn.option-idle:hover {
    border-color: #818cf8;
    background: rgba(129, 140, 248, 0.06);
    color: #f1f5f9;
    transform: translateY(-1px);
  }
  .option-btn.option-correct {
    border-color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
    color: #bbf7d0;
  }
  .option-btn.option-wrong {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    color: #fecaca;
  }
  .option-btn.option-selected {
    border-color: #60a5fa;
    background: rgba(96, 165, 250, 0.1);
    color: #dbeafe;
  }
  .option-btn.option-faded {
    opacity: 0.55;
  }
  .option-btn:disabled { cursor: default; }

  .option-label {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.65rem;
    height: 1.65rem;
    border-radius: 6px;
    background: #1e293b;
    font-size: 0.72rem;
    font-weight: 700;
    color: #94a3b8;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
  }
  .option-correct .option-label {
    background: rgba(34, 197, 94, 0.22);
    color: #86efac;
  }
  .option-wrong .option-label {
    background: rgba(239, 68, 68, 0.22);
    color: #fca5a5;
  }

  .option-text { flex: 1; }

  .option-mark {
    font-weight: 700;
    font-size: 1rem;
    flex-shrink: 0;
  }
  .option-mark-ok { color: #22c55e; }
  .option-mark-bad { color: #ef4444; }

  /* ── True / False ── */
  .tf-row {
    display: flex;
    gap: 0.75rem;
  }
  .tf-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem 1rem;
    border: 1px solid #334155;
    border-radius: 10px;
    background: #0f1117;
    color: #cbd5e1;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 120ms ease, background 120ms ease,
                color 120ms ease, transform 120ms ease;
    position: relative;
  }
  .tf-shortcut {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 6px;
    background: #1e293b;
    color: #94a3b8;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
  }
  .tf-btn.option-idle:hover {
    border-color: #818cf8;
    background: rgba(129, 140, 248, 0.06);
    color: #f1f5f9;
    transform: translateY(-1px);
  }
  .tf-btn.option-correct {
    border-color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
    color: #bbf7d0;
  }
  .tf-btn.option-wrong {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    color: #fecaca;
  }
  .tf-btn.option-selected {
    border-color: #60a5fa;
    background: rgba(96, 165, 250, 0.1);
    color: #dbeafe;
  }
  .tf-btn.option-correct .tf-shortcut {
    background: rgba(34, 197, 94, 0.22);
    color: #86efac;
  }
  .tf-btn.option-wrong .tf-shortcut {
    background: rgba(239, 68, 68, 0.22);
    color: #fca5a5;
  }
  .tf-btn.option-faded { opacity: 0.55; }
  .tf-btn:disabled { cursor: default; }

  /* ── Explanation ── */
  .explanation-box {
    margin-top: 1.25rem;
    padding: 1rem 1.125rem;
    border-radius: 10px;
    border-left: 3px solid #334155;
    background: rgba(15, 17, 23, 0.7);
  }
  .explanation-box.explanation-correct {
    border-left-color: #22c55e;
    background: rgba(34, 197, 94, 0.06);
  }
  .explanation-box.explanation-wrong {
    border-left-color: #ef4444;
    background: rgba(239, 68, 68, 0.06);
  }
  .explanation-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.4rem;
  }
  .explanation-correct .explanation-label { color: #4ade80; }
  .explanation-wrong .explanation-label { color: #f87171; }
  .explanation-body {
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.65;
  }
  .explanation-body :global(.prose) { padding: 0; }

  /* ── Question action row ── */
  .question-actions {
    margin-top: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    justify-content: flex-end;
  }

  /* ── Keyboard hints ── */
  .kbd-hint {
    font-size: 0.72rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }
  .kbd-hint-inline { margin-right: auto; }
  .kbd-hint-strip {
    margin-top: 1rem;
    padding-top: 0.9rem;
    border-top: 1px dashed #1e293b;
    color: #64748b;
    font-size: 0.72rem;
    text-align: center;
  }
  .kbd-inline { margin-left: 0.35rem; }
  kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.1rem;
    padding: 0.05rem 0.35rem;
    margin: 0 0.05rem;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 0.72rem;
    color: #cbd5e1;
    background: #1e293b;
    border: 1px solid #334155;
    border-bottom-width: 2px;
    border-radius: 4px;
    line-height: 1;
  }

  /* ── Results hero ── */
  .results-hero {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 1.25rem;
    align-items: center;
    background: linear-gradient(180deg, rgba(96, 165, 250, 0.06), #131720 70%);
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
  }
  .results-hero-pass {
    background: linear-gradient(180deg, rgba(34, 197, 94, 0.08), #131720 70%);
    border-color: rgba(34, 197, 94, 0.3);
  }
  .results-hero-fail {
    background: linear-gradient(180deg, rgba(234, 179, 8, 0.06), #131720 70%);
    border-color: rgba(234, 179, 8, 0.25);
  }
  .results-hero-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 999px;
    background: rgba(96, 165, 250, 0.12);
    color: #60a5fa;
    flex-shrink: 0;
  }
  .results-hero-pass .results-hero-icon {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
  }
  .results-hero-fail .results-hero-icon {
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
  }
  .results-hero-body { min-width: 0; }
  .results-hero-eyebrow {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.25rem;
  }
  .results-hero-pass .results-hero-eyebrow { color: #4ade80; }
  .results-hero-fail .results-hero-eyebrow { color: #facc15; }

  .results-hero-score {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    font-variant-numeric: tabular-nums;
  }
  .results-hero-num {
    font-size: 2.2rem;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1;
  }
  .results-hero-divider {
    font-size: 1.2rem;
    color: #94a3b8;
  }
  .results-hero-pct {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    margin-left: 0.4rem;
    padding: 0.15rem 0.5rem;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 999px;
  }
  .results-hero-sub {
    margin-top: 0.45rem;
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.5;
  }
  .results-hero-side {
    min-width: 160px;
    flex-shrink: 0;
  }
  .results-bar-track {
    position: relative;
    height: 10px;
    background: #1e293b;
    border-radius: 999px;
    overflow: hidden;
  }
  .results-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #818cf8, #60a5fa);
    border-radius: 999px;
    transition: width 700ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .results-hero-pass .results-bar-fill {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }
  .results-hero-fail .results-bar-fill {
    background: linear-gradient(90deg, #ca8a04, #facc15);
  }
  .results-bar-threshold {
    position: absolute;
    top: -2px;
    width: 2px;
    height: 14px;
    background: rgba(255, 255, 255, 0.35);
    border-radius: 1px;
    transform: translateX(-1px);
  }
  .results-best {
    margin-top: 0.45rem;
    font-size: 0.75rem;
    color: #94a3b8;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
  @media (max-width: 540px) {
    .results-hero {
      grid-template-columns: 1fr;
      text-align: left;
    }
    .results-hero-side { min-width: 0; }
    .results-best { text-align: left; }
  }

  /* ── Action row ── */
  .results-actions-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.75rem;
    flex-wrap: wrap;
  }
  .results-nudge {
    font-size: 0.82rem;
    color: #94a3b8;
  }

  /* ── Review ── */
  .review-section { margin-bottom: 2rem; }

  .review-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
  }
  .review-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0;
    letter-spacing: -0.005em;
  }
  .review-filter {
    display: inline-flex;
    background: #0f1117;
    border: 1px solid #1e293b;
    border-radius: 6px;
    overflow: hidden;
  }
  .review-filter-btn {
    background: transparent;
    border: none;
    color: #94a3b8;
    padding: 0.35rem 0.7rem;
    font-size: 0.78rem;
    cursor: pointer;
    transition: background 120ms ease, color 120ms ease;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }
  .review-filter-btn:hover:not(:disabled) {
    background: #1e293b;
    color: #cbd5e1;
  }
  .review-filter-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .review-filter-active {
    background: rgba(96, 165, 250, 0.12) !important;
    color: #93c5fd !important;
  }
  .review-filter-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.2rem;
    height: 1.2rem;
    padding: 0 0.35rem;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 999px;
    font-size: 0.7rem;
    color: #cbd5e1;
    font-variant-numeric: tabular-nums;
  }
  .review-filter-active .review-filter-count {
    background: rgba(147, 197, 253, 0.2);
    color: #bfdbfe;
  }

  .review-empty {
    padding: 1.5rem;
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    background: #131720;
    border: 1px dashed #1e293b;
    border-radius: 10px;
  }

  .review-card {
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    margin-bottom: 0.65rem;
    overflow: hidden;
    transition: border-color 120ms ease;
  }
  .review-card-correct { border-left: 3px solid #22c55e; }
  .review-card-wrong { border-left: 3px solid #ef4444; }
  .review-card:hover { border-color: #334155; }

  .review-summary {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    width: 100%;
    padding: 0.7rem 1rem;
    background: transparent;
    border: none;
    color: #e2e8f0;
    cursor: pointer;
    text-align: left;
    font-size: 0.88rem;
  }
  .review-summary:hover { background: rgba(148, 163, 184, 0.05); }

  .review-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.4rem;
    height: 1.4rem;
    border-radius: 4px;
    background: #1e293b;
    color: #94a3b8;
    font-size: 0.72rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }

  .review-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.2rem 0.5rem;
    border-radius: 999px;
    flex-shrink: 0;
  }
  .review-status-ok {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
  }
  .review-status-bad {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
  }

  .review-stem-clip {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #cbd5e1;
    min-width: 0;
  }
  .review-chevron {
    color: #64748b;
    font-size: 0.8rem;
    flex-shrink: 0;
  }

  .review-body {
    padding: 0.5rem 1.1rem 1.1rem;
    border-top: 1px solid #1e293b;
    background: rgba(15, 17, 23, 0.6);
  }
  .review-stem {
    color: #e2e8f0;
    font-size: 0.92rem;
    line-height: 1.65;
    margin-bottom: 0.85rem;
  }
  .review-stem :global(.prose) { padding: 0; }

  .review-answers {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin-bottom: 0.85rem;
  }
  @media (max-width: 480px) {
    .review-answers { grid-template-columns: 1fr; }
  }
  .review-answer {
    background: #0f1117;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.55rem 0.75rem;
  }
  .review-answer-correct {
    border-color: rgba(34, 197, 94, 0.35);
    background: rgba(34, 197, 94, 0.05);
  }
  .review-answer-wrong {
    border-color: rgba(239, 68, 68, 0.35);
    background: rgba(239, 68, 68, 0.05);
  }
  .review-answer-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 0.25rem;
    font-weight: 600;
  }
  .review-answer-correct .review-answer-label { color: #4ade80; }
  .review-answer-wrong .review-answer-label { color: #f87171; }
  .review-answer-text {
    color: #e2e8f0;
    font-size: 0.88rem;
    line-height: 1.45;
  }
  .review-answer-blank {
    color: #64748b;
    font-style: italic;
  }

  .review-explanation {
    background: rgba(15, 17, 23, 0.6);
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.55rem 0.85rem 0.85rem;
  }
  .review-explanation-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #818cf8;
    margin-bottom: 0.15rem;
    font-weight: 600;
  }
  .review-explanation :global(.prose) {
    padding: 0;
    font-size: 0.87rem;
    color: #cbd5e1;
  }

  /* ── Footer ── */
  .quiz-footer {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid #1e293b;
  }
</style>
