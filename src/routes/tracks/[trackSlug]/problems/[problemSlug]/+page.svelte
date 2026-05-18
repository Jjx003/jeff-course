<script lang="ts">
  /**
   * Problem page — the main exercise view.
   *
   * Layout:
   *   Header
   *   SplitPane
   *     left:  TabGroup (Problem / Theory / Tips) + ProblemNav
   *     right: LanguageSwitcher + CodeEditor + action bar + OutputPanel
   *
   * All persistence (drafts, run history, submissions) is handled client-side
   * via the service layer. The server only supplies static course content.
   */
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  import Header from '$lib/components/Header.svelte';
  import SplitPane from '$lib/components/SplitPane.svelte';
  import TabGroup from '$lib/components/TabGroup.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import CodeEditor from '$lib/components/CodeEditor.svelte';
  import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
  import OutputPanel from '$lib/components/OutputPanel.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import ReadingView from '$lib/components/ReadingView.svelte';
  import RewardToast from '$lib/components/RewardToast.svelte';
  import StudyTimeTracker from '$lib/components/StudyTimeTracker.svelte';
  import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';

  import type { Language } from '$lib/types/course.js';
  import type { RunSnapshot, SubmitSnapshot } from '$lib/types/execution.js';
  import type { Achievement } from '$lib/types/gamification.js';
  import type { PageData } from './$types';

  const POINTS_BY_DIFFICULTY: Record<string, number> = {
    beginner: 10,
    intermediate: 20,
    advanced: 35
  };

  let { data }: { data: PageData } = $props();

  let track        = $derived(data.track);
  let problem      = $derived(data.problem);
  let prevProblem  = $derived(data.prevProblem);
  let nextProblem  = $derived(data.nextProblem);
  let isReading    = $derived(problem.type === 'reading');

  // ── Problem ID ────────────────────────────────────────────────────────
  let problemId = $derived(`${track.slug}/${problem.slug}`);

  // ── Language state ────────────────────────────────────────────────────
  let currentLanguage = $state<Language>('python');
  // Set proper default once problem is available (skipped for reading modules,
  // which have no editor and may carry placeholder language values).
  $effect.pre(() => {
    if (!isReading) currentLanguage = problem.defaultLanguage;
  });

  // ── Editor ref ────────────────────────────────────────────────────────
  let editorRef = $state<CodeEditor | undefined>(undefined);
  let editorInitialValue = $derived(problem.starterCode[problem.defaultLanguage] ?? '');

  // ── Output state ─────────────────────────────────────────────────────
  let latestRun = $state<RunSnapshot | null>(null);
  let latestSubmit = $state<SubmitSnapshot | null>(null);
  let submissions = $state<SubmitSnapshot[]>([]); // accepted only, for the dropdown

  // ── Submissions dropdown ──────────────────────────────────────────────
  let showSubmissions = $state(false);

  // ── Reset starter-code confirmation ───────────────────────────────────
  let showResetConfirm = $state(false);

  function openResetConfirm() {
    showResetConfirm = true;
  }

  async function performReset() {
    if (!editorRef) return;
    const starter = problem.starterCode[currentLanguage] ?? '';
    editorRef.setValue(starter);
    if (services) {
      await services.draftStorage.saveDraft(problemId, currentLanguage, starter);
    }
  }

  // ── Running / submitting state ────────────────────────────────────────
  let isRunning = $state(false);
  let isSubmitting = $state(false);

  // ── Reward toast ──────────────────────────────────────────────────────
  let toastRef = $state<RewardToast | undefined>(undefined);
  /** Whether this problem was already solved when the page loaded. Seeded
   *  from SSR so re-submits never trigger the first-solve toast. */
  let wasAlreadySolved = $state(false);
  /** Snapshot of unlocked achievement IDs taken on mount; used to detect new unlocks. */
  let knownAchievementIds = $state<Set<string>>(new Set());

  // ── Editor font size ──────────────────────────────────────────────────
  const FONT_SIZE_MIN = 10;
  const FONT_SIZE_MAX = 24;
  let editorFontSize = $state(14);
  function zoomIn()  { editorFontSize = Math.min(FONT_SIZE_MAX, editorFontSize + 1); }
  function zoomOut() { editorFontSize = Math.max(FONT_SIZE_MIN, editorFontSize - 1); }

  // ── Output panel resize ───────────────────────────────────────────────
  const OUTPUT_MIN = 60;
  const OUTPUT_MAX = 700;
  let outputHeight = $state(220);
  let outputCollapsed = $state(false);
  let outputResizing = $state(false);
  let editorPane = $state<HTMLDivElement | undefined>(undefined);

  function onOutputResizerDown(e: MouseEvent) {
    e.preventDefault();
    outputResizing = true;
  }
  function onOutputResizerMove(e: MouseEvent) {
    if (!outputResizing || !editorPane) return;
    const rect = editorPane.getBoundingClientRect();
    const h = Math.max(OUTPUT_MIN, Math.min(OUTPUT_MAX, rect.bottom - e.clientY));
    outputHeight = h;
    if (outputCollapsed && h > OUTPUT_MIN + 10) outputCollapsed = false;
  }
  function onOutputResizerUp() {
    if (!outputResizing) return;
    outputResizing = false;
    if (browser) {
      localStorage.setItem('output-panel-height', String(outputHeight));
      localStorage.setItem('output-panel-collapsed', String(outputCollapsed));
    }
  }
  function toggleOutput() {
    outputCollapsed = !outputCollapsed;
    if (browser) localStorage.setItem('output-panel-collapsed', String(outputCollapsed));
  }

  // ── Tab state ─────────────────────────────────────────────────────────
  let TABS = $derived([
    { id: 'problem',  label: 'Problem'  },
    { id: 'theory',   label: 'Theory'   },
    { id: 'tips',     label: 'Tips'     },
    ...(problem.tabs.solution ? [{ id: 'solution', label: 'Solution' }] : [])
  ]);
  let activeTabId = $state('problem');

  // Solution gate
  let solutionRevealed = $state(false);

  // ── Services (client-side only) ───────────────────────────────────────
  // Imported lazily to avoid SSR issues
  let services: typeof import('$lib/services/index.js') | null = null;

  onMount(async () => {
    // Seed first-solve guard from SSR before any user interaction.
    wasAlreadySolved = data.initiallyCompleted ?? false;

    services = await import('$lib/services/index.js');

    // Snapshot current achievements (used by both reading & coding views).
    try {
      const summary = await services.statsService.getSummary();
      knownAchievementIds = new Set(
        summary.achievements.filter((a) => a.unlockedAt !== null).map((a) => a.id)
      );
    } catch {
      // non-fatal — toasts just won't show
    }

    // Reading modules have no editor, runner, or drafts — stop here.
    if (isReading) return;

    // Restore output panel size/state
    const savedH = localStorage.getItem('output-panel-height');
    if (savedH) outputHeight = Math.max(OUTPUT_MIN, Math.min(OUTPUT_MAX, parseInt(savedH)));
    const savedC = localStorage.getItem('output-panel-collapsed');
    if (savedC) outputCollapsed = savedC === 'true';

    // Restore latest run and accepted submissions on page load
    const [savedRuns, savedSubmissions] = await Promise.all([
      services.runHistoryStorage.getRuns(problemId),
      services.submissionStorage.getSubmissions(problemId)
    ]);
    latestRun = savedRuns[0] ?? null;
    submissions = savedSubmissions;
    latestSubmit = savedSubmissions[0] ?? null;
    wasAlreadySolved = savedSubmissions.length > 0;

    // Load saved draft for the default language
    await loadDraftIntoEditor(problem.defaultLanguage);
  });

  // ── Reset state when navigating between problems ──────────────────────
  // SvelteKit reuses this +page.svelte component across [problemSlug]
  // changes, so onMount only runs once. Without this effect, the Monaco
  // editor keeps the previous problem's starter code, and the run/submit
  // panels show stale results when the user clicks Prev/Next.
  let lastSeenProblemId = $state(problemId);
  $effect(() => {
    if (problemId === lastSeenProblemId) return;
    lastSeenProblemId = problemId;

    latestRun = null;
    latestSubmit = null;
    submissions = [];
    solutionRevealed = false;
    activeTabId = 'problem';
    showSubmissions = false;

    if (isReading || !services) return;

    const svc = services;
    const pid = problemId;
    void (async () => {
      const [savedRuns, savedSubmissions] = await Promise.all([
        svc.runHistoryStorage.getRuns(pid),
        svc.submissionStorage.getSubmissions(pid)
      ]);
      latestRun = savedRuns[0] ?? null;
      submissions = savedSubmissions;
      latestSubmit = savedSubmissions[0] ?? null;
      wasAlreadySolved = savedSubmissions.length > 0;
      await loadDraftIntoEditor(problem.defaultLanguage);
    })();
  });

  // ── Draft loading ─────────────────────────────────────────────────────

  async function loadDraftIntoEditor(lang: Language) {
    if (!services || !browser) return;
    const draft = await services.draftStorage.getDraft(problemId, lang);
    const code = draft?.code ?? problem.starterCode[lang] ?? '';
    editorInitialValue = code;
    // If editor is already mounted, push the new value directly
    editorRef?.setValue(code);
  }

  // ── Language switching ────────────────────────────────────────────────

  async function handleLanguageChange(lang: Language) {
    if (lang === currentLanguage) return;

    // Save the current draft before switching
    if (services && editorRef) {
      await services.draftStorage.saveDraft(problemId, currentLanguage, editorRef.getValue());
    }

    currentLanguage = lang;
    await loadDraftIntoEditor(lang);
  }

  // ── Auto-save draft ───────────────────────────────────────────────────

  async function handleDraftSave(code: string) {
    if (!services) return;
    await services.draftStorage.saveDraft(problemId, currentLanguage, code);
  }

  // ── Run ───────────────────────────────────────────────────────────────

  async function handleRun() {
    if (!services || !editorRef || isRunning) return;
    isRunning = true;

    try {
      const code = editorRef.getValue();
      const result = await services.executionService.run({
        problemId,
        language: currentLanguage,
        code
      });

      const snapshot: RunSnapshot = {
        id: services.generateId(),
        problemId,
        language: currentLanguage,
        code,
        result,
        timestamp: Date.now()
      };

      latestRun = snapshot;
      await services.runHistoryStorage.addRun(snapshot).catch(() => {});
    } finally {
      isRunning = false;
    }
  }

  // ── Load submission into editor ───────────────────────────────────────

  async function handleLoadSubmission(code: string, language: Language) {
    if (language !== currentLanguage) {
      await handleLanguageChange(language);
    }
    editorRef?.setValue(code);
    showSubmissions = false;
  }

  // ── Submit ────────────────────────────────────────────────────────────

  async function handleSubmit() {
    if (!services || !editorRef || isSubmitting) return;
    isSubmitting = true;

    try {
      const code = editorRef.getValue();
      const result = await services.executionService.submit({
        problemId,
        language: currentLanguage,
        code
      });

      const snapshot: SubmitSnapshot = {
        id: services.generateId(),
        problemId,
        language: currentLanguage,
        code,
        result,
        timestamp: Date.now()
      };

      latestSubmit = snapshot;
      await services.submissionStorage.addSubmission(snapshot).catch(() => {});
      if (snapshot.result.verdict === 'accepted') {
        const isFirstSolve = !wasAlreadySolved;
        submissions = await services.submissionStorage.getSubmissions(problemId).catch(() => submissions);
        wasAlreadySolved = true;

        if (isFirstSolve) {
          const pts = POINTS_BY_DIFFICULTY[problem.difficulty] ?? 10;
          toastRef?.show({
            kind: 'points',
            title: `+${pts} pts`,
            subtitle: 'First solve'
          });
          // After the points toast, look for newly unlocked achievements and
          // queue them with a gentle delay so they don't pile up at once.
          void checkForNewAchievements(1400);
        }
      }
    } finally {
      isSubmitting = false;
    }
  }

  /**
   * Fetch latest stats and surface any achievements unlocked since mount.
   * The server persists the unlock on first GET, so the second time we
   * fetch this same achievement set won't trigger again.
   */
  async function checkForNewAchievements(delayMs: number) {
    if (!services) return;
    await new Promise((r) => setTimeout(r, delayMs));
    try {
      const summary = await services.statsService.getSummary();
      const newOnes: Achievement[] = summary.achievements.filter(
        (a) => a.unlockedAt !== null && !knownAchievementIds.has(a.id)
      );
      // Stagger toasts so each one has a moment in the spotlight.
      for (let i = 0; i < newOnes.length; i++) {
        const a = newOnes[i];
        knownAchievementIds.add(a.id);
        await new Promise((r) => setTimeout(r, i === 0 ? 0 : 3500));
        toastRef?.show({
          kind: 'achievement',
          title: a.title,
          subtitle: a.description
        });
      }
    } catch {
      // non-fatal
    }
  }

  // ── Difficulty badge ──────────────────────────────────────────────────
  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };
</script>

<RewardToast bind:this={toastRef} />

<!-- Study-time tracker. Keyed on problemId so navigating between problems
     ends the current session and starts a fresh one. Works for both
     coding and reading paths since the component renders nothing on
     screen (other than the idle-prompt modal). -->
{#key problemId}
  <StudyTimeTracker {problemId} />
{/key}

{#if isReading}
  <ReadingView
    {track}
    {problem}
    {prevProblem}
    {nextProblem}
    initiallyCompleted={data.initiallyCompleted}
    onMarkedComplete={() => {
      toastRef?.show({
        kind: 'points',
        title: '+5 pts',
        subtitle: 'Reading complete'
      });
      void checkForNewAchievements(1400);
    }}
  />
{:else}
<!-- Full-height shell: header + split pane -->
<div class="page-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <div class="content-area">
    <SplitPane>
      <!-- ── LEFT: Instructions pane ───────────────────────────────── -->
      {#snippet left()}
        <div class="instructions-pane">
          <!-- Problem meta header -->
          <div class="problem-header">
            <h1 class="text-base font-bold text-slate-100 leading-snug">{problem.title}</h1>
            <div class="flex items-center gap-2 mt-1.5 flex-wrap">
              <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
                {problem.difficulty}
              </span>
              <span class="text-xs text-slate-500">{problem.estimatedMinutes} min</span>
              {#each problem.tags as tag}
                <span class="badge badge-blue">{tag}</span>
              {/each}
            </div>
          </div>

          <!-- Tabs -->
          <div class="tab-area">
            <TabGroup tabs={TABS} bind:activeId={activeTabId} children={tabContent} />
            {#snippet tabContent({ activeId }: { activeId: string })}
              <div class="tab-scroll">
                {#if activeId === 'problem'}
                  <MarkdownRenderer content={problem.tabs.problem} />
                {:else if activeId === 'theory'}
                  <MarkdownRenderer content={problem.tabs.theory} />
                {:else if activeId === 'tips'}
                  <MarkdownRenderer content={problem.tabs.tips} />
                {:else if activeId === 'solution'}
                  {#if !solutionRevealed}
                    <!-- Confirm gate -->
                    <div class="solution-gate">
                      <div class="solution-gate-box">
                        <div class="solution-gate-icon">&#128274;</div>
                        <h3 class="solution-gate-title">View Solution?</h3>
                        <p class="solution-gate-body">
                          Revealing the solution before solving the problem yourself will reduce your learning.
                          Only proceed if you are truly stuck or have already solved it.
                        </p>
                        <div class="solution-gate-actions">
                          <button
                            class="btn-ghost"
                            onclick={() => { activeTabId = 'problem'; }}
                          >
                            Go Back
                          </button>
                          <button
                            class="btn-danger"
                            onclick={() => { solutionRevealed = true; }}
                          >
                            Reveal Solution
                          </button>
                        </div>
                      </div>
                    </div>
                  {:else}
                    <!-- Solution content -->
                    <MarkdownRenderer content={problem.tabs.solution ?? ''} />
                    {#if problem.solutionCode}
                      <div class="solution-code-section">
                        <h3 class="solution-code-title">Solution Code</h3>
                        {#each problem.languages as lang}
                          {#if problem.solutionCode[lang]}
                            <div class="solution-code-block">
                              <div class="solution-code-lang-label">{lang === 'python' ? 'Python' : 'C++'}</div>
                              <pre class="solution-code-pre"><code>{problem.solutionCode[lang]}</code></pre>
                            </div>
                          {/if}
                        {/each}
                      </div>
                    {/if}
                  {/if}
                {/if}
              </div>
            {/snippet}
          </div>

          <!-- Prev / Next navigation -->
          <ProblemNav
            trackSlug={track.slug}
            {prevProblem}
            {nextProblem}
          />
        </div>
      {/snippet}

      <!-- ── RIGHT: Editor pane ────────────────────────────────────── -->
      {#snippet right()}
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
          class="editor-pane"
          class:cursor-row-resize={outputResizing}
          bind:this={editorPane}
          onmousemove={onOutputResizerMove}
          onmouseup={onOutputResizerUp}
          onmouseleave={onOutputResizerUp}
          role="presentation"
        >
          <!-- Editor toolbar -->
          <div class="editor-toolbar">
            <LanguageSwitcher
              languages={problem.languages}
              current={currentLanguage}
              onchange={handleLanguageChange}
            />
            <!-- Font size controls -->
            <div class="flex items-center gap-0.5 ml-2">
              <button
                class="zoom-btn"
                onclick={zoomOut}
                disabled={editorFontSize <= FONT_SIZE_MIN}
                title="Decrease font size"
              >−</button>
              <span class="zoom-label">{editorFontSize}</span>
              <button
                class="zoom-btn"
                onclick={zoomIn}
                disabled={editorFontSize >= FONT_SIZE_MAX}
                title="Increase font size"
              >+</button>
            </div>
            <div class="flex items-center gap-2 ml-auto">
              <!-- Reset to starter code -->
              <button
                class="btn-ghost text-xs"
                onclick={openResetConfirm}
                title="Reset editor to the starter code for this problem"
              >
                Reset
              </button>

              <!-- Submissions dropdown -->
              <div class="relative">
                <button
                  class="btn-ghost text-xs"
                  onclick={() => showSubmissions = !showSubmissions}
                  title="View accepted submissions"
                >
                  Submissions
                  {#if submissions.length > 0}
                    <span class="ml-1 badge badge-green">{submissions.length}</span>
                  {/if}
                  <span class="ml-1 text-slate-500">{showSubmissions ? '▲' : '▼'}</span>
                </button>

                {#if showSubmissions}
                  <!-- Backdrop to close on outside click -->
                  <div
                    class="fixed inset-0 z-10"
                    role="presentation"
                    onclick={() => showSubmissions = false}
                  ></div>
                  <!-- Dropdown panel -->
                  <div class="submissions-dropdown z-20">
                    {#if submissions.length === 0}
                      <p class="text-slate-500 italic text-xs px-3 py-2">No accepted submissions yet.</p>
                    {:else}
                      {#each submissions as s}
                        <div class="submission-row">
                          <span class="text-slate-400 text-xs">{new Date(s.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                          <span class="badge badge-blue text-xs">{s.language}</span>
                          {#if s.result.score !== null}
                            <span class="text-green-400 text-xs">{s.result.score}/100</span>
                          {/if}
                          <button
                            class="ml-auto text-xs text-accent-400 hover:text-accent-300 border border-accent-600 hover:border-accent-400 rounded px-2 py-0.5 transition-colors"
                            onclick={() => handleLoadSubmission(s.code, s.language)}
                          >
                            Load
                          </button>
                        </div>
                      {/each}
                    {/if}
                  </div>
                {/if}
              </div>

              <button
                class="btn-ghost"
                onclick={handleRun}
                disabled={isRunning}
                title="Run code (Ctrl+Enter)"
              >
                {#if isRunning}
                  <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-600 border-t-slate-200"></span>
                {:else}
                  <span>▶</span>
                {/if}
                Run
              </button>
              <button
                class="btn-success"
                onclick={handleSubmit}
                disabled={isSubmitting}
              >
                {#if isSubmitting}
                  <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-green-800 border-t-white"></span>
                {:else}
                  <span>↑</span>
                {/if}
                Submit
              </button>
            </div>
          </div>

          <!-- Monaco editor — grows to fill space -->
          <div class="editor-area">
            <CodeEditor
              bind:this={editorRef}
              language={currentLanguage}
              initialValue={editorInitialValue}
              fontSize={editorFontSize}
              onsave={handleDraftSave}
            />
          </div>

          <!-- Output resize handle -->
          <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
          <div
            class="output-resizer"
            role="separator"
            aria-label="Resize output panel"
            onmousedown={onOutputResizerDown}
          >
            <button
              class="output-toggle"
              onclick={toggleOutput}
              onmousedown={(e) => e.stopPropagation()}
              title={outputCollapsed ? 'Expand output' : 'Collapse output'}
            >{outputCollapsed ? '▲ Output' : '▼'}</button>
          </div>

          <!-- Output panel — resizable -->
          {#if !outputCollapsed}
            <div class="output-area" style="height: {outputHeight}px">
              <OutputPanel
                {latestRun}
                {latestSubmit}
              />
            </div>
          {/if}
        </div>
      {/snippet}
    </SplitPane>
  </div>

  <ConfirmDialog
    bind:open={showResetConfirm}
    title="Reset to starter code?"
    body="Your current code will be replaced with the original starter for this problem. This cannot be undone."
    confirmLabel="Reset"
    cancelLabel="Cancel"
    tone="danger"
    onConfirm={performReset}
  />
</div>
{/if}

<style>
  .page-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .content-area {
    flex: 1;
    overflow: hidden;
  }

  /* ── Left pane ── */
  .instructions-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #131720;
    border-right: 1px solid #1e293b;
    overflow: hidden;
  }

  .problem-header {
    padding: 1rem 1.25rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    flex-shrink: 0;
  }

  .tab-area {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .tab-scroll {
    overflow-y: auto;
    height: 100%;
  }

  /* ── Right pane ── */
  .editor-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #0f1117;
    overflow: hidden;
  }

  .editor-toolbar {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    flex-shrink: 0;
    gap: 0.5rem;
    background: #131720;
  }

  .editor-area {
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  .output-resizer {
    flex-shrink: 0;
    height: 6px;
    background: #1e293b;
    cursor: row-resize;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
  }
  .output-resizer:hover {
    background: #2d3f5e;
  }

  .output-toggle {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    padding: 0 0.4rem;
    height: 18px;
    font-size: 0.65rem;
    color: #64748b;
    background: #131720;
    border: 1px solid #2d3748;
    border-radius: 3px;
    cursor: pointer;
    white-space: nowrap;
    line-height: 1;
    display: flex;
    align-items: center;
  }
  .output-toggle:hover {
    color: #94a3b8;
    border-color: #475569;
  }

  .output-area {
    flex-shrink: 0;
    overflow: hidden;
  }

  /* ── Zoom controls ── */
  :global(.zoom-btn) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 4px;
    font-size: 1rem;
    line-height: 1;
    color: #94a3b8;
    background: transparent;
    border: 1px solid #334155;
    cursor: pointer;
    transition: background 0.1s, color 0.1s;
  }
  :global(.zoom-btn:hover:not(:disabled)) {
    background: #1e293b;
    color: #e2e8f0;
  }
  :global(.zoom-btn:disabled) {
    opacity: 0.3;
    cursor: not-allowed;
  }
  .zoom-label {
    min-width: 2rem;
    text-align: center;
    font-size: 0.7rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }

  /* ── Submissions dropdown ── */
  .submissions-dropdown {
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    min-width: 320px;
    max-height: 280px;
    background: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 6px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    overflow-y: auto;
  }

  .submission-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1e293b;
  }

  .submission-row:last-child {
    border-bottom: none;
  }

  .submission-row:hover {
    background: #1e2535;
  }

  /* ── Solution gate ── */
  .solution-gate {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 2rem 1.5rem;
  }

  .solution-gate-box {
    text-align: center;
    max-width: 340px;
  }

  .solution-gate-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    filter: grayscale(0.3);
  }

  .solution-gate-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.75rem;
  }

  .solution-gate-body {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .solution-gate-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
  }

  /* ── Solution code section ── */
  .solution-code-section {
    padding: 0 1.25rem 1.5rem;
    border-top: 1px solid #1e293b;
    margin-top: 0.5rem;
  }

  .solution-code-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #e2e8f0;
    padding: 1rem 0 0.75rem;
  }

  .solution-code-block {
    margin-bottom: 1rem;
  }

  .solution-code-lang-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 0.35rem;
  }

  .solution-code-pre {
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    overflow-x: auto;
    font-size: 0.8rem;
    line-height: 1.6;
    color: #c9d1d9;
    white-space: pre;
  }
</style>
