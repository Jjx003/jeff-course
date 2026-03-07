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

  import type { Language } from '$lib/types/course.js';
  import type { RunSnapshot, SubmitSnapshot } from '$lib/types/execution.js';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let track        = $derived(data.track);
  let problem      = $derived(data.problem);
  let prevProblem  = $derived(data.prevProblem);
  let nextProblem  = $derived(data.nextProblem);

  // ── Problem ID ────────────────────────────────────────────────────────
  let problemId = $derived(`${track.slug}/${problem.slug}`);

  // ── Language state ────────────────────────────────────────────────────
  let currentLanguage = $state<Language>('python');
  // Set proper default once problem is available
  $effect.pre(() => { currentLanguage = problem.defaultLanguage; });

  // ── Editor ref ────────────────────────────────────────────────────────
  let editorRef: CodeEditor;
  let editorInitialValue = $derived(problem.starterCode[problem.defaultLanguage] ?? '');

  // ── Output state ─────────────────────────────────────────────────────
  let latestRun = $state<RunSnapshot | null>(null);
  let latestSubmit = $state<SubmitSnapshot | null>(null);
  let runs = $state<RunSnapshot[]>([]);
  let submissions = $state<SubmitSnapshot[]>([]);

  // ── Running / submitting state ────────────────────────────────────────
  let isRunning = $state(false);
  let isSubmitting = $state(false);

  // ── Tab state ─────────────────────────────────────────────────────────
  const TABS = [
    { id: 'problem', label: 'Problem' },
    { id: 'theory',  label: 'Theory'  },
    { id: 'tips',    label: 'Tips'    }
  ];
  let activeTabId = $state('problem');

  // ── Services (client-side only) ───────────────────────────────────────
  // Imported lazily to avoid SSR issues
  let services: typeof import('$lib/services/index.js') | null = null;

  onMount(async () => {
    services = await import('$lib/services/index.js');

    // Restore latest history snapshots for the output panel
    const [savedRuns, savedSubmissions] = await Promise.all([
      services.runHistoryStorage.getRuns(problemId),
      services.submissionStorage.getSubmissions(problemId)
    ]);
    runs = savedRuns;
    submissions = savedSubmissions;
    latestRun = savedRuns[0] ?? null;
    latestSubmit = savedSubmissions[0] ?? null;

    // Load saved draft for the default language
    await loadDraftIntoEditor(problem.defaultLanguage);
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

    await services.runHistoryStorage.addRun(snapshot);
    runs = await services.runHistoryStorage.getRuns(problemId);
    latestRun = snapshot;

    isRunning = false;
  }

  // ── Submit ────────────────────────────────────────────────────────────

  async function handleSubmit() {
    if (!services || !editorRef || isSubmitting) return;
    isSubmitting = true;

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

    await services.submissionStorage.addSubmission(snapshot);
    submissions = await services.submissionStorage.getSubmissions(problemId);
    latestSubmit = snapshot;

    isSubmitting = false;
  }

  // ── Difficulty badge ──────────────────────────────────────────────────
  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };
</script>

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
        <div class="editor-pane">
          <!-- Editor toolbar -->
          <div class="editor-toolbar">
            <LanguageSwitcher
              languages={problem.languages}
              current={currentLanguage}
              onchange={handleLanguageChange}
            />
            <div class="flex items-center gap-2 ml-auto">
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
              onsave={handleDraftSave}
            />
          </div>

          <!-- Output panel — fixed height at bottom -->
          <div class="output-area">
            <OutputPanel
              {latestRun}
              {latestSubmit}
              {runs}
              {submissions}
            />
          </div>
        </div>
      {/snippet}
    </SplitPane>
  </div>
</div>

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

  .output-area {
    height: 220px;
    flex-shrink: 0;
    border-top: 1px solid #1e293b;
    overflow: hidden;
  }
</style>
