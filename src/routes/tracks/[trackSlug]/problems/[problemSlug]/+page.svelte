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
  import { onDestroy, onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { beforeNavigate } from '$app/navigation';

  import Header from '$lib/components/Header.svelte';
  import SplitPane from '$lib/components/SplitPane.svelte';
  import TabGroup from '$lib/components/TabGroup.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import CodeEditor from '$lib/components/CodeEditor.svelte';
  import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
  import OutputPanel from '$lib/components/OutputPanel.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import ReadingView from '$lib/components/ReadingView.svelte';
  import QuizView from '$lib/components/QuizView.svelte';
  import RewardToast from '$lib/components/RewardToast.svelte';
  import StudyTimeTracker from '$lib/components/StudyTimeTracker.svelte';
  import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';

  import type { Language } from '$lib/types/course.js';
  import type { RunSnapshot, SubmitSnapshot, RunResult, SubmitResult } from '$lib/types/execution.js';
  import type { Achievement } from '$lib/types/gamification.js';
  import type {
    LogChunk,
    ResourceLimits,
    SandboxCapabilities,
    SandboxMode,
    SessionRecord,
    SessionStatus
  } from '$lib/types/sandbox.js';
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
  let isQuiz       = $derived(problem.type === 'quiz');

  // ── Problem ID ────────────────────────────────────────────────────────
  let problemId = $derived(`${track.slug}/${problem.slug}`);

  // ── Language state ────────────────────────────────────────────────────
  let currentLanguage = $state<Language>('python');
  // Set proper default once problem is available (skipped for reading/quiz modules,
  // which have no editor and may carry placeholder language values).
  $effect.pre(() => {
    if (!isReading && !isQuiz) currentLanguage = problem.defaultLanguage;
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

  /**
   * The id of the currently in-flight sandbox session, or null if nothing
   * is running. We track this so the navigation/unmount handlers can
   * dispatch a cancel to the server (which tree-kills the child process
   * even when the SSE connection is already torn down).
   */
  let activeSessionId = $state<string | null>(null);
  /** Unsubscribe callback for the active SSE log stream. */
  let unsubscribeStream: (() => void) | null = null;
  /** Stable status string from the most recent SSE `status` event. */
  let liveStatus = $state<SessionStatus | null>(null);

  function isExecutionLive(): boolean {
    return activeSessionId !== null;
  }

  // ── Run mode + resource picker ────────────────────────────────────────
  //
  // Per-track preference: stored on the server in `sandbox_preferences`,
  // seeded on mount via GET /api/sandbox/preferences/[trackSlug] and pushed
  // back via PUT whenever the user changes anything. The defaults come from
  // `defaultResourcesFor(mode)` on the server side; we mirror the same
  // numbers here so the UI never has to wait for a fetch before being
  // usable.

  const DEFAULT_RESOURCES: Record<SandboxMode, ResourceLimits> = {
    baremetal:    { memoryMb: 0,      cpus: 0, gpu: 'none', timeoutMs: 60_000   },
    docker:       { memoryMb: 4096,   cpus: 2, gpu: 'none', timeoutMs: 600_000  },
    'docker-gpu': { memoryMb: 16_384, cpus: 4, gpu: 'all',  timeoutMs: 1_200_000 }
  };

  let runMode = $state<SandboxMode>('baremetal');
  let memoryMb = $state<number>(DEFAULT_RESOURCES.baremetal.memoryMb);
  let cpus = $state<number>(DEFAULT_RESOURCES.baremetal.cpus);
  let timeoutMs = $state<number>(DEFAULT_RESOURCES.baremetal.timeoutMs);
  let gpuDevice = $state<'all' | number>('all');
  let showAdvanced = $state(false);

  let capabilities = $state<SandboxCapabilities | null>(null);
  /** Per-session-only dismissal of the "Docker not detected" banner. */
  let dockerBannerDismissed = $state(false);
  /** Suppresses the PUT during the initial preference seed. */
  let preferenceLoaded = $state(false);

  function modeLabel(mode: SandboxMode): string {
    if (mode === 'baremetal') return 'baremetal';
    if (mode === 'docker') return 'container';
    if (mode === 'docker-gpu') return 'container + GPU';
    return mode;
  }

  function isModeAvailable(mode: SandboxMode): boolean {
    if (mode === 'baremetal') return true;
    if (!capabilities) return true; // optimistic until probed
    if (mode === 'docker') return capabilities.docker.available;
    if (mode === 'docker-gpu') return capabilities.docker.available && capabilities.gpu.available;
    return false;
  }

  function modeUnavailableReason(mode: SandboxMode): string {
    if (!capabilities) return '';
    if (mode === 'docker' && !capabilities.docker.available) {
      return capabilities.docker.reason ?? 'Docker not available';
    }
    if (mode === 'docker-gpu') {
      if (!capabilities.docker.available) return capabilities.docker.reason ?? 'Docker not available';
      if (!capabilities.gpu.available) return capabilities.gpu.reason ?? 'GPU passthrough not available';
    }
    return '';
  }

  /**
   * Apply the per-mode defaults to the local sliders. Used both on the
   * initial preference fetch and whenever the user picks a different
   * mode from the segmented control.
   */
  function applyModeDefaults(mode: SandboxMode) {
    const d = DEFAULT_RESOURCES[mode];
    memoryMb = d.memoryMb;
    cpus = d.cpus;
    timeoutMs = d.timeoutMs;
    if (mode === 'docker-gpu') {
      gpuDevice = 'all';
    }
  }

  function selectRunMode(mode: SandboxMode) {
    if (!isModeAvailable(mode)) return;
    if (mode === runMode) return;
    runMode = mode;
    applyModeDefaults(mode);
  }

  async function savePreference() {
    if (!services || !preferenceLoaded) return;
    const gpu: ResourceLimits['gpu'] = runMode === 'docker-gpu'
      ? (gpuDevice === 'all' ? 'all' : { device: gpuDevice })
      : 'none';
    try {
      await services.sessionsService.setPreference({
        trackSlug: track.slug,
        preferredMode: runMode,
        resources: { memoryMb, cpus, gpu, timeoutMs }
      });
    } catch {
      // non-fatal — picker stays usable even if the PUT fails.
    }
  }

  /**
   * Push the preference whenever any of the relevant fields changes. We
   * gate on `preferenceLoaded` so the initial seed doesn't immediately
   * overwrite the server state with our local defaults.
   */
  $effect(() => {
    if (!browser || !preferenceLoaded) return;
    // Read every dependency so $effect re-runs on any change.
    runMode; memoryMb; cpus; timeoutMs; gpuDevice;
    void savePreference();
  });

  function resourcesForStart(): ResourceLimits {
    const gpu: ResourceLimits['gpu'] = runMode === 'docker-gpu'
      ? (gpuDevice === 'all' ? 'all' : { device: gpuDevice })
      : 'none';
    return { memoryMb, cpus, gpu, timeoutMs };
  }

  /**
   * The preferences endpoint returns a "default" baremetal preference when
   * no row exists for this track. We use this helper to detect that case
   * so we can fall back to the module's `runtime.recommendedMode` hint.
   */
  function isDefaultPreference(pref: import('$lib/types/sandbox.js').TrackPreference): boolean {
    const d = DEFAULT_RESOURCES.baremetal;
    return pref.preferredMode === 'baremetal'
      && pref.resources.memoryMb === d.memoryMb
      && pref.resources.cpus === d.cpus
      && pref.resources.timeoutMs === d.timeoutMs
      && pref.resources.gpu === d.gpu;
  }

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

    // Reading and quiz modules have no editor, runner, or drafts — stop here.
    if (isReading || isQuiz) return;

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

    // Sandbox capabilities + per-track preference. Both are best-effort —
    // if either fetch fails we silently fall back to baremetal defaults.
    void services.sessionsService.capabilities()
      .then((caps) => { capabilities = caps; })
      .catch(() => { capabilities = null; });

    try {
      const pref = await services.sessionsService.getPreference(track.slug);
      // The API returns a "default" preference (baremetal) for first-visit
      // tracks. We treat it as "no real preference" only when it matches
      // the baked-in defaults exactly. Otherwise the user has explicitly
      // saved something and we honor it as-is.
      const hasRealPreference = pref && !isDefaultPreference(pref);
      if (hasRealPreference && pref) {
        // Apply mode first, then layer the persisted resources on top of
        // the per-mode defaults so any field the user never touched stays
        // sensible.
        runMode = pref.preferredMode;
        applyModeDefaults(pref.preferredMode);
        memoryMb = pref.resources.memoryMb ?? memoryMb;
        cpus = pref.resources.cpus ?? cpus;
        timeoutMs = pref.resources.timeoutMs ?? timeoutMs;
        if (pref.preferredMode === 'docker-gpu') {
          const g = pref.resources.gpu;
          if (g === 'all') gpuDevice = 'all';
          else if (typeof g === 'object' && g.device !== undefined) gpuDevice = g.device;
        }
      } else if (problem.runtime?.recommendedMode && isModeAvailable(problem.runtime.recommendedMode)) {
        // No saved per-track preference yet — fall back to the module
        // author's recommendation if it's actually usable on this host.
        const hint = problem.runtime;
        const hintMode = hint.recommendedMode!;
        runMode = hintMode;
        applyModeDefaults(hintMode);
        const r = hint.resources;
        if (r) {
          if (typeof r.memoryMb === 'number') memoryMb = r.memoryMb;
          if (typeof r.cpus === 'number') cpus = r.cpus;
          if (typeof r.timeoutMs === 'number') timeoutMs = r.timeoutMs;
          if (hintMode === 'docker-gpu' && r.gpu) {
            if (r.gpu === 'all') gpuDevice = 'all';
            else if (typeof r.gpu === 'object' && r.gpu.device !== undefined) gpuDevice = r.gpu.device;
          }
        }
      } else {
        applyModeDefaults('baremetal');
      }
    } catch {
      applyModeDefaults('baremetal');
    } finally {
      preferenceLoaded = true;
    }

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

    if (isReading || isQuiz || !services) return;

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
  //
  // Switched from the legacy single-shot /api/execute call to the new
  // sandbox session pipeline. The flow is:
  //   1. sessionsService.start(...) — POST /api/sessions, get an id back
  //   2. subscribe via SSE — chunks fan in for live tail
  //   3. on the `exit` event — fetch the final SessionRecord for verdict
  //
  // While the session is running we mutate `latestRun.result.stdout/stderr`
  // in place; Svelte 5's $state proxy re-renders OutputPanel on each chunk.

  function statusToRunStatus(status: SessionStatus, exitCode: number | null): RunResult['status'] {
    if (status === 'completed' && exitCode === 0) return 'ok';
    if (status === 'killed') return 'timeout';
    return 'error';
  }

  async function handleRun() {
    if (!services || !editorRef || isRunning || activeSessionId) return;
    isRunning = true;
    liveStatus = null;

    const code = editorRef.getValue();
    const startedAt = Date.now();

    // Seed an empty snapshot so the Output panel renders the live tail
    // as chunks arrive. We mutate result.stdout/result.stderr in place.
    const snapshot: RunSnapshot = {
      id: services.generateId(),
      problemId,
      language: currentLanguage,
      code,
      result: {
        stdout: '',
        stderr: '',
        durationMs: null,
        success: false,
        status: 'ok'
      },
      timestamp: startedAt
    };
    latestRun = snapshot;

    let sessionId: string;
    try {
      const started = await services.sessionsService.start({
        problemId,
        language: currentLanguage,
        code,
        action: 'run',
        mode: runMode,
        resources: resourcesForStart()
      });
      sessionId = started.id;
    } catch (err) {
      snapshot.result.stderr = err instanceof Error ? err.message : String(err);
      snapshot.result.status = 'error';
      isRunning = false;
      return;
    }
    activeSessionId = sessionId;

    await new Promise<void>((resolve) => {
      const unsub = services!.sessionsService.subscribe(sessionId, async (chunk: LogChunk) => {
        if (chunk.kind === 'stdout') {
          latestRun!.result.stdout += chunk.data;
        } else if (chunk.kind === 'stderr') {
          latestRun!.result.stderr += chunk.data;
        } else if (chunk.kind === 'status') {
          liveStatus = chunk.status;
        } else if (chunk.kind === 'exit') {
          const rec = await services!.sessionsService.get(sessionId).catch(() => null);
          const finalStatus = rec?.status ?? 'completed';
          latestRun!.result.durationMs = chunk.durationMs;
          latestRun!.result.status = statusToRunStatus(finalStatus, chunk.exitCode);
          latestRun!.result.success = finalStatus === 'completed' && chunk.exitCode === 0;
          resolve();
        }
      });
      unsubscribeStream = unsub;
    });

    if (unsubscribeStream) {
      unsubscribeStream();
      unsubscribeStream = null;
    }
    activeSessionId = null;
    isRunning = false;
    liveStatus = null;

    // Persist the run snapshot so it shows up after a page refresh.
    await services.runHistoryStorage.addRun(snapshot).catch(() => {});
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
    if (!services || !editorRef || isSubmitting || activeSessionId) return;
    isSubmitting = true;
    liveStatus = null;

    const code = editorRef.getValue();
    const startedAt = Date.now();

    // Live snapshot: result mutates as chunks arrive. We pre-populate
    // verdict='pending' / message='Running…' so the UI shows progress
    // immediately. The final verdict comes from the SessionRecord on exit.
    const submitSnapshot: SubmitSnapshot = {
      id: services.generateId(),
      problemId,
      language: currentLanguage,
      code,
      result: {
        verdict: 'pending',
        message: 'Running…',
        score: null
      },
      timestamp: startedAt
    };
    latestSubmit = submitSnapshot;

    // Run tab mirrors stdout/stderr live so the user can watch progress.
    const runSnapshot: RunSnapshot = {
      id: services.generateId(),
      problemId,
      language: currentLanguage,
      code,
      result: { stdout: '', stderr: '', durationMs: null, success: false, status: 'ok' },
      timestamp: startedAt
    };
    latestRun = runSnapshot;

    let sessionId: string;
    try {
      const started = await services.sessionsService.start({
        problemId,
        language: currentLanguage,
        code,
        action: 'submit',
        mode: runMode,
        resources: resourcesForStart()
      });
      sessionId = started.id;
    } catch (err) {
      submitSnapshot.result = {
        verdict: 'error',
        message: err instanceof Error ? err.message : String(err),
        score: null
      };
      isSubmitting = false;
      return;
    }
    activeSessionId = sessionId;

    // Captured in the closure below and read after the promise settles.
    const finalRecordRef: { value: SessionRecord | null } = { value: null };
    await new Promise<void>((resolve) => {
      const unsub = services!.sessionsService.subscribe(sessionId, async (chunk: LogChunk) => {
        if (chunk.kind === 'stdout') {
          latestRun!.result.stdout += chunk.data;
        } else if (chunk.kind === 'stderr') {
          latestRun!.result.stderr += chunk.data;
        } else if (chunk.kind === 'status') {
          liveStatus = chunk.status;
        } else if (chunk.kind === 'exit') {
          finalRecordRef.value = await services!.sessionsService.get(sessionId).catch(() => null);
          latestRun!.result.durationMs = chunk.durationMs;
          const fStatus = finalRecordRef.value?.status ?? 'completed';
          latestRun!.result.status = statusToRunStatus(fStatus, chunk.exitCode);
          latestRun!.result.success = fStatus === 'completed' && chunk.exitCode === 0;
          resolve();
        }
      });
      unsubscribeStream = unsub;
    });
    const finalRecord = finalRecordRef.value;

    if (unsubscribeStream) {
      unsubscribeStream();
      unsubscribeStream = null;
    }
    activeSessionId = null;
    isSubmitting = false;
    liveStatus = null;

    // Build the final SubmitResult from the record's verdict fields.
    const verdict = finalRecord?.submitVerdict ?? 'error';
    const message = finalRecord?.submitMessage ?? 'Submission completed.';
    const score = finalRecord?.submitScore ?? null;
    const submitResult: SubmitResult = {
      verdict,
      message,
      score: verdict === 'pending' ? null : score,
      testResults: verdict === 'pending' ? undefined : [
        {
          name: 'Expected output comparison',
          passed: verdict === 'accepted',
          actual: runSnapshot.result.stdout,
          durationMs: runSnapshot.result.durationMs ?? undefined
        }
      ]
    };
    submitSnapshot.result = submitResult;

    await services.submissionStorage.addSubmission(submitSnapshot).catch(() => {});
    if (submitResult.verdict === 'accepted') {
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
        void checkForNewAchievements(1400);
      }
    }
  }

  // ── In-flight execution lifecycle ─────────────────────────────────────
  //
  // With the sessions pipeline the SSE connection is decoupled from the
  // running child process: closing the stream doesn't stop the sandbox
  // session by itself. We must explicitly POST /api/sessions/[id]/cancel
  // to tear down the underlying spawn / container.
  //
  // Three scenarios where we need to cancel:
  //   1. Client-side navigation: beforeNavigate → confirm → cancel.
  //   2. Tab close / reload: beforeunload prompt + best-effort cancel via
  //      sendBeacon-equivalent fetch (browsers may interrupt, but the
  //      server-side AbortSignal on the SSE will also fire on disconnect).
  //   3. Component teardown for other reasons (HMR, etc): silent cancel.

  function cancelActiveSession() {
    if (!activeSessionId || !services) return;
    void services.sessionsService.cancel(activeSessionId);
    if (unsubscribeStream) {
      unsubscribeStream();
      unsubscribeStream = null;
    }
  }

  beforeNavigate(({ cancel }) => {
    if (!isExecutionLive()) return;
    const ok = browser
      ? confirm(`A ${modeLabel(runMode)} run is still in progress. Cancel it and leave the page?`)
      : true;
    if (!ok) {
      cancel();
      return;
    }
    cancelActiveSession();
  });

  onDestroy(() => {
    cancelActiveSession();
  });

  $effect(() => {
    if (!browser) return;
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!isExecutionLive()) return;
      // Browsers ignore custom strings since 2017 and just show a generic
      // "Leave site?" prompt, but the preventDefault + returnValue dance
      // is still what triggers it.
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  });

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
{:else if isQuiz}
  <QuizView
    {track}
    {problem}
    {prevProblem}
    {nextProblem}
    quizQuestions={problem.quizQuestions ?? []}
    initiallyCompleted={data.initiallyCompleted}
    initialProgress={data.initialQuizProgress}
    onPassed={(score, total) => {
      toastRef?.show({
        kind: 'points',
        title: '+5 pts',
        subtitle: `Quiz passed · ${score}/${total}`
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
                  <MarkdownRenderer content={problem.tabs.problem} variant="study" />
                {:else if activeId === 'theory'}
                  <MarkdownRenderer content={problem.tabs.theory} variant="study" />
                {:else if activeId === 'tips'}
                  <MarkdownRenderer content={problem.tabs.tips} variant="study" />
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
                    <MarkdownRenderer content={problem.tabs.solution ?? ''} variant="study" />
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
          <!-- Docker-missing banner: only when capabilities are loaded and
               docker is unavailable, and the user hasn't dismissed it. -->
          {#if capabilities && !capabilities.docker.available && !dockerBannerDismissed}
            <div class="docker-banner">
              <span>
                Container runtime not detected. Install
                <a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer">Docker Desktop</a>
                to enable sandboxed execution.
                {#if capabilities.docker.reason}<span class="docker-banner-reason"> ({capabilities.docker.reason})</span>{/if}
              </span>
              <button
                class="docker-banner-dismiss"
                aria-label="Dismiss banner"
                onclick={() => { dockerBannerDismissed = true; }}
              >×</button>
            </div>
          {/if}

          <!-- Editor toolbar -->
          <div class="editor-toolbar">
            <LanguageSwitcher
              languages={problem.languages}
              current={currentLanguage}
              onchange={handleLanguageChange}
            />
            <!-- Run-mode segmented control + advanced panel -->
            <div class="run-mode-wrap">
              <div class="segmented" role="group" aria-label="Run mode">
                {#each ['baremetal', 'docker', 'docker-gpu'] as const as m}
                  {@const available = isModeAvailable(m)}
                  {@const reason = modeUnavailableReason(m)}
                  <button
                    type="button"
                    class="segment"
                    class:segment-active={runMode === m}
                    class:segment-disabled={!available}
                    disabled={!available}
                    onclick={() => selectRunMode(m)}
                    title={available
                      ? `Use ${modeLabel(m)} for Run / Submit`
                      : `${modeLabel(m)} unavailable: ${reason}`}
                  >
                    {m === 'baremetal' ? 'Baremetal' : m === 'docker' ? 'Container' : 'Container + GPU'}
                  </button>
                {/each}
              </div>
              <button
                type="button"
                class="advanced-toggle"
                onclick={() => { showAdvanced = !showAdvanced; }}
                title="Show resource limits"
              >
                Advanced {showAdvanced ? '▴' : '▾'}
              </button>
            </div>
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

          {#if showAdvanced}
            <div class="advanced-panel">
              <label class="advanced-field">
                <span>Memory (MB)</span>
                <input
                  type="number"
                  min="0"
                  step="256"
                  bind:value={memoryMb}
                  disabled={runMode === 'baremetal'}
                  title={runMode === 'baremetal' ? 'Memory limits only apply to container modes.' : ''}
                />
              </label>
              <label class="advanced-field">
                <span>CPUs</span>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  bind:value={cpus}
                  disabled={runMode === 'baremetal'}
                  title={runMode === 'baremetal' ? 'CPU limits only apply to container modes.' : ''}
                />
              </label>
              <label class="advanced-field">
                <span>Timeout (s)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={Math.round(timeoutMs / 1000)}
                  oninput={(e) => {
                    const v = parseInt((e.currentTarget as HTMLInputElement).value, 10);
                    if (!isNaN(v) && v > 0) timeoutMs = v * 1000;
                  }}
                />
              </label>
              {#if runMode === 'docker-gpu'}
                <label class="advanced-field">
                  <span>GPU device</span>
                  <select
                    bind:value={gpuDevice}
                  >
                    <option value="all">all</option>
                    {#if capabilities?.gpu.deviceCount}
                      {#each Array(capabilities.gpu.deviceCount) as _, idx}
                        <option value={idx}>device {idx}</option>
                      {/each}
                    {/if}
                  </select>
                </label>
              {/if}
            </div>
          {/if}

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
                {liveStatus}
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
    min-height: 0;
    height: 100%;
    overflow: hidden;
    overscroll-behavior: none;
  }

  .content-area {
    flex: 1;
    min-height: 0;
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
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .tab-scroll {
    overflow-y: auto;
    overscroll-behavior: contain;
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
    flex-wrap: wrap;
  }

  /* ── Run-mode picker ── */
  .run-mode-wrap {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }
  .segmented {
    display: inline-flex;
    align-items: stretch;
    background: #0f1117;
    border: 1px solid #334155;
    border-radius: 6px;
    overflow: hidden;
  }
  .segment {
    padding: 0.3rem 0.65rem;
    font-size: 0.72rem;
    font-weight: 500;
    color: #94a3b8;
    background: transparent;
    border: none;
    border-right: 1px solid #1e293b;
    cursor: pointer;
    transition: color 0.1s, background 0.1s;
    white-space: nowrap;
  }
  .segment:last-child { border-right: none; }
  .segment:hover:not(:disabled) {
    background: #1e293b;
    color: #e2e8f0;
  }
  .segment-active {
    background: #1e3a5f !important;
    color: #93c5fd !important;
  }
  .segment-disabled {
    color: #475569 !important;
    cursor: not-allowed;
  }
  .advanced-toggle {
    font-size: 0.7rem;
    color: #94a3b8;
    background: transparent;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.25rem 0.55rem;
    cursor: pointer;
    transition: color 0.1s, background 0.1s, border-color 0.1s;
  }
  .advanced-toggle:hover {
    color: #e2e8f0;
    background: #1e293b;
    border-color: #475569;
  }

  /* ── Advanced panel ── */
  .advanced-panel {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    background: #0f1623;
  }
  .advanced-field {
    display: inline-flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 0.65rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .advanced-field input,
  .advanced-field select {
    background: #0d1117;
    border: 1px solid #334155;
    border-radius: 4px;
    color: #e2e8f0;
    padding: 0.25rem 0.5rem;
    font-size: 0.78rem;
    font-variant-numeric: tabular-nums;
    text-transform: none;
    letter-spacing: 0;
    min-width: 90px;
  }
  .advanced-field input:focus,
  .advanced-field select:focus {
    outline: none;
    border-color: #60a5fa;
  }
  .advanced-field input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* ── Docker banner ── */
  .docker-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.45rem 0.8rem;
    background: #422006;
    color: #fde68a;
    border-bottom: 1px solid #b45309;
    font-size: 0.75rem;
  }
  .docker-banner a {
    color: #fcd34d;
    text-decoration: underline;
  }
  .docker-banner a:hover {
    color: #fde68a;
  }
  .docker-banner-reason {
    color: #fcd34d;
    opacity: 0.85;
  }
  .docker-banner-dismiss {
    background: transparent;
    border: none;
    color: #fcd34d;
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0 0.35rem;
  }
  .docker-banner-dismiss:hover {
    color: #fde68a;
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
