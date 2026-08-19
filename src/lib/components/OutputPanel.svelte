<script lang="ts">
  /**
   * OutputPanel
   *
   * Two views on the last execution:
   *
   *   Output — the program's own console, replayed in arrival order so
   *            stdout and stderr interleave the way they would in a
   *            terminal, tailing live while the session runs.
   *   Result — the grader's verdict: a plain-language headline plus a real
   *            expected-vs-actual comparison instead of a raw diff blob.
   *
   * Submission history is surfaced in the toolbar dropdown, not here.
   */
  import { tick } from 'svelte';
  import type { LogLine, RunSnapshot, SubmitSnapshot, DiffRow } from '$lib/types/execution.js';
  import type { SessionStatus } from '$lib/types/sandbox.js';
  import { parseGraderMessage, countMismatches, firstMismatchIndex } from '$lib/execution/graderDiff.js';

  type Tab = 'output' | 'result';

  interface Props {
    latestRun?: RunSnapshot | null;
    latestSubmit?: SubmitSnapshot | null;
    /** Status of the live session, if one is running. Drives the badge. */
    liveStatus?: SessionStatus | null;
    /** True while a Run is in flight. */
    isRunning?: boolean;
    /** True while a Submit is in flight. */
    isSubmitting?: boolean;
    /** Bound by the page so Run/Submit can bring their own view forward. */
    activeTab?: Tab;
    /** Ask the page to stop the in-flight session. */
    oncancel?: () => void;
  }

  let {
    latestRun = null,
    latestSubmit = null,
    liveStatus = null,
    isRunning = false,
    isSubmitting = false,
    activeTab = $bindable('output'),
    oncancel
  }: Props = $props();

  let isLive = $derived(isRunning || isSubmitting);

  // ── Live elapsed clock ──────────────────────────────────────────────
  // Ticks only while something is running; the final duration comes from
  // the exit event, so we stop touching it once the session settles.
  let nowMs = $state(Date.now());
  $effect(() => {
    if (!isLive) return;
    const t = setInterval(() => { nowMs = Date.now(); }, 100);
    return () => clearInterval(t);
  });

  function fmtDuration(ms: number): string {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
    const mins = Math.floor(ms / 60_000);
    const secs = Math.round((ms % 60_000) / 1000);
    return `${mins}m ${secs}s`;
  }

  let elapsedLabel = $derived.by(() => {
    if (isLive && latestRun) return fmtDuration(Math.max(0, nowMs - latestRun.timestamp));
    if (latestRun?.result.durationMs != null) return fmtDuration(latestRun.result.durationMs);
    return null;
  });

  function liveStatusLabel(s: SessionStatus): string {
    switch (s) {
      case 'queued':    return 'Waiting for a free slot';
      case 'starting':  return 'Starting up';
      case 'running':   return 'Running';
      case 'completed': return 'Finished';
      case 'cancelled': return 'Cancelled';
      case 'killed':    return 'Timed out';
      case 'failed':    return 'Exited with an error';
      case 'crashed':   return 'Crashed';
      default:          return s;
    }
  }

  // ── Console log ─────────────────────────────────────────────────────
  // Newer runs carry a chronological `log`; rows written before that field
  // existed only have the two concatenated streams, so fall back to those.
  let logLines = $derived.by<LogLine[]>(() => {
    if (!latestRun) return [];
    const { log, stdout, stderr } = latestRun.result;
    if (log?.length) return log;
    const out: LogLine[] = [];
    if (stdout) out.push({ stream: 'stdout', text: stdout });
    if (stderr) out.push({ stream: 'stderr', text: stderr });
    return out;
  });

  let hasOutput = $derived(logLines.some((l) => l.text.length > 0));

  // ── Stick-to-bottom tailing ─────────────────────────────────────────
  let logScroll = $state<HTMLElement | undefined>(undefined);
  let stickToBottom = $state(true);

  function onLogScroll() {
    if (!logScroll) return;
    const distanceFromBottom = logScroll.scrollHeight - logScroll.scrollTop - logScroll.clientHeight;
    stickToBottom = distanceFromBottom < 24;
  }

  $effect(() => {
    // Re-run whenever new output arrives.
    logLines.length;
    latestRun?.result.stdout.length;
    latestRun?.result.stderr.length;
    if (!stickToBottom || activeTab !== 'output') return;
    void tick().then(() => {
      if (logScroll) logScroll.scrollTop = logScroll.scrollHeight;
    });
  });

  // ── Grader verdict ──────────────────────────────────────────────────
  let parsed = $derived.by(() => {
    const r = latestSubmit?.result;
    if (!r) return null;
    // Prefer the structured fields the page builds; fall back to parsing the
    // raw grader message for submissions saved by older builds.
    if (r.diff || r.summary) {
      return {
        summary: r.summary ?? r.message,
        diff: r.diff ?? null,
        expectedText: r.expectedText ?? '',
        actualText: r.actualText ?? ''
      };
    }
    return parseGraderMessage(r.message);
  });

  let diffRows = $derived<DiffRow[]>(parsed?.diff ?? []);
  let mismatchCount = $derived(diffRows.length ? countMismatches(diffRows) : 0);
  let firstBadRow = $derived(diffRows.length ? firstMismatchIndex(diffRows) : -1);
  let firstBadLine = $derived.by(() => {
    if (firstBadRow < 0) return null;
    const row = diffRows[firstBadRow];
    return row.expectedNo ?? row.actualNo ?? null;
  });

  // Result tab has something new to show — used for the tab dot.
  let hasVerdict = $derived(!!latestSubmit);

  type Tone = 'pass' | 'fail' | 'error' | 'neutral' | 'busy';

  let verdictView = $derived.by<{ tone: Tone; icon: string; title: string; detail: string } | null>(() => {
    if (!latestSubmit) return null;
    const r = latestSubmit.result;

    if (isSubmitting) {
      return { tone: 'busy', icon: '', title: 'Grading your submission…', detail: 'Your program is running against the expected output.' };
    }
    if (r.verdict === 'accepted') {
      return {
        tone: 'pass',
        icon: '✓',
        title: 'Accepted',
        detail: 'Every line of your output matched what this module expects.'
      };
    }
    if (r.verdict === 'wrong_answer') {
      const total = diffRows.length;
      const detail = mismatchCount > 0
        ? `${mismatchCount} of ${total} line${total === 1 ? '' : 's'} differ` +
          (firstBadLine ? ` — first difference on line ${firstBadLine}.` : '.')
        : 'Your program ran fine, but its output is not what the module expects.';
      return { tone: 'fail', icon: '✕', title: 'Output does not match', detail };
    }
    if (r.verdict === 'pending') {
      return {
        tone: 'neutral',
        icon: 'ⓘ',
        title: 'Not automatically graded',
        detail: r.summary ?? r.message ?? 'This module has no fixed expected output, so there is nothing to compare against. Check your results against the problem statement, or ask the tutor.'
      };
    }
    // error
    const status = latestRun?.result.status;
    if (status === 'timeout') {
      return {
        tone: 'error',
        icon: '⏱',
        title: 'Timed out',
        detail: 'Your program was still running when the time limit was reached. Look for an unbounded loop, or raise the timeout under Advanced.'
      };
    }
    if (status === 'cancelled') {
      return {
        tone: 'neutral',
        icon: '■',
        title: 'Stopped',
        detail: 'You stopped this submission before it finished, so there is nothing to grade yet.'
      };
    }
    return {
      tone: 'error',
      icon: '!',
      title: 'Your program did not finish',
      detail: 'It exited with an error before producing a gradeable result. The error output is below.'
    };
  });

  /**
   * The error text to show on an error verdict. The grader stuffs captured
   * stderr into the message, but the live run usually has the fuller copy.
   */
  let errorText = $derived.by(() => {
    const r = latestSubmit?.result;
    if (!r) return '';
    if (r.stderr) return r.stderr.trim();
    if (latestRun?.result.stderr) return latestRun.result.stderr.trim();
    return (parsed?.summary ?? '').trim();
  });

  /**
   * Last line of a Python traceback is the one that names the exception —
   * worth pulling to the top so the user does not have to read upward.
   */
  let errorHeadline = $derived.by(() => {
    const lines = errorText.split('\n').map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return null;
    const last = lines[lines.length - 1];
    return /^[A-Za-z_.]*(Error|Exception|Warning)\b/.test(last) ? last : null;
  });

  // ── Diff display options ────────────────────────────────────────────
  let diffLayout = $state<'unified' | 'split'>('unified');
  let showAllLines = $state(false);

  const CONTEXT = 2;

  /** Rows to render, with long runs of identical lines folded away. */
  let visibleRows = $derived.by<Array<{ row: DiffRow; index: number } | { fold: number }>>(() => {
    if (!diffRows.length) return [];
    if (showAllLines) return diffRows.map((row, index) => ({ row, index }));

    const keep = new Array<boolean>(diffRows.length).fill(false);
    diffRows.forEach((r, i) => {
      if (r.kind === 'same') return;
      for (let j = Math.max(0, i - CONTEXT); j <= Math.min(diffRows.length - 1, i + CONTEXT); j++) {
        keep[j] = true;
      }
    });

    const out: Array<{ row: DiffRow; index: number } | { fold: number }> = [];
    let folded = 0;
    diffRows.forEach((row, index) => {
      if (keep[index]) {
        if (folded) { out.push({ fold: folded }); folded = 0; }
        out.push({ row, index });
      } else {
        folded++;
      }
    });
    if (folded) out.push({ fold: folded });
    return out;
  });

  let foldedCount = $derived(diffRows.filter((r) => r.kind === 'same').length - visibleRows.filter((v) => 'row' in v && v.row.kind === 'same').length);

  // ── Copy ────────────────────────────────────────────────────────────
  let copiedKey = $state<string | null>(null);

  async function copy(key: string, text: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      copiedKey = key;
      setTimeout(() => { if (copiedKey === key) copiedKey = null; }, 1500);
    } catch {
      // Clipboard can be blocked (insecure origin, denied permission).
      // The text is selectable on screen either way.
    }
  }

  function consoleText(): string {
    return logLines.map((l) => l.text).join('');
  }

  function resultText(): string {
    if (!latestSubmit || !parsed) return '';
    const parts = [`${verdictView?.title ?? latestSubmit.result.verdict}: ${verdictView?.detail ?? ''}`];
    if (diffRows.length) {
      parts.push('', '--- expected', '+++ actual');
      for (const r of diffRows) {
        if (r.kind === 'same') parts.push(`  ${r.expected}`);
        else {
          if (r.expected !== undefined) parts.push(`- ${r.expected}`);
          if (r.actual !== undefined) parts.push(`+ ${r.actual}`);
        }
      }
    } else if (errorText) {
      parts.push('', errorText);
    }
    return parts.join('\n');
  }

  let copyTarget = $derived(activeTab === 'output' ? consoleText() : resultText());

  function rowClass(kind: DiffRow['kind']): string {
    switch (kind) {
      case 'changed': return 'row-changed';
      case 'missing': return 'row-missing';
      case 'extra':   return 'row-extra';
      default:        return 'row-same';
    }
  }

  /** Renders trailing spaces visibly — a classic invisible cause of failure. */
  function showTrailing(text: string): string {
    return text.replace(/[ \t]+$/, (ws) => '·'.repeat(ws.length));
  }
</script>

<div class="output-panel-wrap">
  <!-- ── Tab bar ── -->
  <div class="panel-head">
    <button
      class="tab-btn text-xs py-1.5 px-3"
      class:active={activeTab === 'output'}
      onclick={() => activeTab = 'output'}
    >
      Output
      {#if isRunning}<span class="live-dot"></span>{/if}
    </button>
    <button
      class="tab-btn text-xs py-1.5 px-3"
      class:active={activeTab === 'result'}
      onclick={() => activeTab = 'result'}
    >
      Result
      {#if isSubmitting}
        <span class="live-dot"></span>
      {:else if hasVerdict}
        <span
          class="verdict-dot"
          class:dot-pass={latestSubmit?.result.verdict === 'accepted'}
          class:dot-fail={latestSubmit?.result.verdict === 'wrong_answer'}
          class:dot-error={latestSubmit?.result.verdict === 'error'}
        ></span>
      {/if}
    </button>

    <!-- Status chip: what the runner is doing right now -->
    <div class="head-status">
      {#if isLive}
        <span class="chip chip-live">
          <span class="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse"></span>
          {liveStatus ? liveStatusLabel(liveStatus) : 'Starting up'}
          {#if elapsedLabel}<span class="chip-time">{elapsedLabel}</span>{/if}
        </span>
        {#if oncancel}
          <button class="stop-btn" onclick={oncancel} title="Stop the running program">Stop</button>
        {/if}
      {:else if latestRun}
        <span
          class="chip"
          class:chip-pass={latestRun.result.status === 'ok'}
          class:chip-warn={latestRun.result.status === 'timeout' || latestRun.result.status === 'cancelled'}
          class:chip-fail={latestRun.result.status === 'error'}
        >
          {latestRun.result.status === 'ok'
            ? 'Finished cleanly'
            : latestRun.result.status === 'timeout'
              ? 'Timed out'
              : latestRun.result.status === 'cancelled'
                ? 'Stopped'
                : `Exited with an error${latestRun.result.exitCode != null ? ` (code ${latestRun.result.exitCode})` : ''}`}
          {#if elapsedLabel}<span class="chip-time">{elapsedLabel}</span>{/if}
        </span>
      {/if}
    </div>

    <button
      class="copy-btn"
      onclick={() => copy(activeTab, copyTarget)}
      disabled={!copyTarget}
      title={activeTab === 'output' ? 'Copy console output' : 'Copy the grader result'}
    >
      {copiedKey === activeTab ? '✓ Copied' : 'Copy'}
    </button>
  </div>

  <!-- ── Output tab ── -->
  {#if activeTab === 'output'}
    <div class="output-body output-panel" bind:this={logScroll} onscroll={onLogScroll}>
      {#if !latestRun}
        <p class="empty-hint">
          Nothing has run yet. Press <kbd>Ctrl</kbd>+<kbd>Enter</kbd> to run your code,
          or <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Enter</kbd> to submit it for grading.
        </p>
      {:else if !hasOutput}
        {#if isLive}
          <p class="empty-hint">Waiting for output…</p>
        {:else}
          <p class="empty-hint">Your program finished without printing anything.</p>
        {/if}
      {:else}
        <div class="console">
          {#each logLines as line, i (i)}
            <span class:stream-err={line.stream === 'stderr'}>{line.text}</span>
          {/each}
        </div>
      {/if}

      {#if latestRun && !isLive && latestRun.result.status !== 'ok' && logLines.some((l) => l.stream === 'stderr')}
        <p class="stream-note">
          Lines in amber came from stderr — for Python that is where tracebacks and
          package-install chatter go, so not every amber line is a failure.
        </p>
      {/if}
    </div>
  {/if}

  <!-- ── Result tab ── -->
  {#if activeTab === 'result'}
    <div class="output-body">
      {#if !latestSubmit || !verdictView}
        <p class="empty-hint">
          No submission yet. Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Enter</kbd> (or Submit)
          to check your solution against the module's expected output.
        </p>
      {:else}
        <div class="verdict verdict-{verdictView.tone}">
          <span class="verdict-icon">
            {#if verdictView.tone === 'busy'}
              <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-600 border-t-slate-200"></span>
            {:else}
              {verdictView.icon}
            {/if}
          </span>
          <div class="verdict-text">
            <div class="verdict-title">
              {verdictView.title}
              {#if latestSubmit.result.score !== null && latestSubmit.result.verdict !== 'pending'}
                <span class="verdict-score">{latestSubmit.result.score}/100</span>
              {/if}
            </div>
            <p class="verdict-detail">{verdictView.detail}</p>
          </div>
        </div>

        <!-- Wrong answer: the comparison -->
        {#if diffRows.length}
          <div class="diff-toolbar">
            <div class="diff-legend">
              <span class="legend-swatch legend-expected"></span> expected
              <span class="legend-swatch legend-actual"></span> your output
            </div>
            <div class="diff-actions">
              <button
                class="mini-btn"
                class:mini-active={diffLayout === 'unified'}
                onclick={() => diffLayout = 'unified'}
              >Unified</button>
              <button
                class="mini-btn"
                class:mini-active={diffLayout === 'split'}
                onclick={() => diffLayout = 'split'}
              >Side by side</button>
              {#if foldedCount > 0 || showAllLines}
                <button class="mini-btn" onclick={() => showAllLines = !showAllLines}>
                  {showAllLines ? 'Only differences' : 'All lines'}
                </button>
              {/if}
              <button
                class="mini-btn"
                onclick={() => copy('expected', parsed?.expectedText ?? '')}
              >{copiedKey === 'expected' ? '✓' : 'Copy expected'}</button>
              <button
                class="mini-btn"
                onclick={() => copy('actual', parsed?.actualText ?? '')}
              >{copiedKey === 'actual' ? '✓' : 'Copy yours'}</button>
            </div>
          </div>

          {#if diffLayout === 'unified'}
            <div class="diff diff-unified">
              {#each visibleRows as item, i (i)}
                {#if 'fold' in item}
                  <button class="fold-row" onclick={() => showAllLines = true}>
                    ⋯ {item.fold} matching line{item.fold === 1 ? '' : 's'} hidden
                  </button>
                {:else}
                  {@const row = item.row}
                  {#if row.kind === 'same'}
                    <div class="dline row-same">
                      <span class="gutter">{row.expectedNo ?? ''}</span>
                      <span class="marker"> </span>
                      <span class="dtext">{showTrailing(row.expected ?? '')}</span>
                    </div>
                  {:else}
                    {#if row.expected !== undefined}
                      <div class="dline row-expected">
                        <span class="gutter">{row.expectedNo ?? ''}</span>
                        <span class="marker">−</span>
                        <span class="dtext">{showTrailing(row.expected)}</span>
                      </div>
                    {/if}
                    {#if row.actual !== undefined}
                      <div class="dline row-actual">
                        <span class="gutter">{row.actualNo ?? ''}</span>
                        <span class="marker">+</span>
                        <span class="dtext">{showTrailing(row.actual)}</span>
                      </div>
                    {/if}
                    <!-- Explain the gap once per run, not once per line —
                         a ten-line stray block does not need ten notes. -->
                    {#if diffRows[item.index - 1]?.kind !== row.kind}
                      {#if row.kind === 'missing'}
                        <div class="dline row-note"><span class="gutter"></span><span class="marker"></span><span class="dtext">your output has nothing here</span></div>
                      {:else if row.kind === 'extra'}
                        <div class="dline row-note"><span class="gutter"></span><span class="marker"></span><span class="dtext">the expected output has nothing here</span></div>
                      {/if}
                    {/if}
                  {/if}
                {/if}
              {/each}
            </div>
          {:else}
            <div class="diff diff-split">
              <div class="split-head">
                <span>Expected</span>
                <span>Your output</span>
              </div>
              {#each visibleRows as item, i (i)}
                {#if 'fold' in item}
                  <button class="fold-row" onclick={() => showAllLines = true}>
                    ⋯ {item.fold} matching line{item.fold === 1 ? '' : 's'} hidden
                  </button>
                {:else}
                  {@const row = item.row}
                  <div class="split-row {rowClass(row.kind)}">
                    <div class="split-cell">
                      <span class="gutter">{row.expectedNo ?? ''}</span>
                      <span class="dtext">{row.expected !== undefined ? showTrailing(row.expected) : ''}</span>
                    </div>
                    <div class="split-cell">
                      <span class="gutter">{row.actualNo ?? ''}</span>
                      <span class="dtext">{row.actual !== undefined ? showTrailing(row.actual) : ''}</span>
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}

        <!-- Error: the traceback, most useful line first -->
        {:else if latestSubmit.result.verdict === 'error' && errorText}
          {#if errorHeadline}
            <div class="error-headline">{errorHeadline}</div>
          {/if}
          <pre class="error-body">{errorText}</pre>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .output-panel-wrap {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    background: #0d0f10;
  }

  .panel-head {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem 0;
    border-bottom: 1px solid #1e293b;
    flex-shrink: 0;
  }

  .head-status {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding-bottom: 0.25rem;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.7rem;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    border: 1px solid #1e293b;
    background: #131720;
    color: #94a3b8;
    white-space: nowrap;
  }
  .chip-time  { color: #64748b; }
  .chip-live  { border-color: #1e3a8a; color: #93c5fd; }
  .chip-pass  { border-color: #14532d; color: #86efac; }
  .chip-warn  { border-color: #713f12; color: #fcd34d; }
  .chip-fail  { border-color: #7f1d1d; color: #fca5a5; }

  .stop-btn {
    font-size: 0.7rem;
    padding: 0.125rem 0.5rem;
    border-radius: 0.25rem;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
    transition: background-color 0.15s;
  }
  .stop-btn:hover { background: #450a0a; }

  .copy-btn {
    margin-left: 0.375rem;
    margin-bottom: 0.25rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.7rem;
    border-radius: 0.25rem;
    color: #94a3b8;
    transition: all 0.15s;
  }
  .copy-btn:hover:not(:disabled) { color: #e2e8f0; background: #1e293b; }
  .copy-btn:disabled { opacity: 0.3; }

  .live-dot, .verdict-dot {
    display: inline-block;
    width: 0.375rem;
    height: 0.375rem;
    border-radius: 9999px;
    margin-left: 0.375rem;
    vertical-align: middle;
  }
  .live-dot   { background: #60a5fa; animation: pulse 1.2s ease-in-out infinite; }
  .dot-pass   { background: #4ade80; }
  .dot-fail   { background: #f87171; }
  .dot-error  { background: #fbbf24; }

  @keyframes pulse { 50% { opacity: 0.35; } }

  .output-body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 0.75rem 1rem;
    color: #cbd5e1;
  }

  .empty-hint {
    color: #64748b;
    font-size: 0.8rem;
    line-height: 1.6;
  }

  .empty-hint kbd {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    padding: 0.05rem 0.3rem;
    border: 1px solid #334155;
    border-bottom-width: 2px;
    border-radius: 0.25rem;
    color: #94a3b8;
    background: #131720;
  }

  /* ── Console ── */
  .console {
    white-space: pre-wrap;
    word-break: break-word;
    user-select: text;
    cursor: text;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.78rem;
    line-height: 1.55;
    color: #d1fae5;
  }

  .stream-err { color: #fcd34d; }

  .stream-note {
    margin-top: 0.75rem;
    padding-top: 0.5rem;
    border-top: 1px dashed #1e293b;
    color: #64748b;
    font-size: 0.7rem;
    line-height: 1.5;
  }

  /* ── Verdict banner ── */
  .verdict {
    display: flex;
    gap: 0.625rem;
    padding: 0.625rem 0.75rem;
    border-radius: 0.375rem;
    border: 1px solid #1e293b;
    background: #131720;
    margin-bottom: 0.75rem;
  }

  .verdict-pass    { border-color: #14532d; background: rgba(20, 83, 45, 0.18); }
  .verdict-fail    { border-color: #7f1d1d; background: rgba(127, 29, 29, 0.16); }
  .verdict-error   { border-color: #713f12; background: rgba(113, 63, 18, 0.16); }
  .verdict-neutral { border-color: #1e3a8a; background: rgba(30, 58, 138, 0.16); }
  .verdict-busy    { border-color: #334155; }

  .verdict-icon {
    flex-shrink: 0;
    width: 1.25rem;
    text-align: center;
    font-size: 0.95rem;
    line-height: 1.4;
  }
  .verdict-pass    .verdict-icon { color: #4ade80; }
  .verdict-fail    .verdict-icon { color: #f87171; }
  .verdict-error   .verdict-icon { color: #fbbf24; }
  .verdict-neutral .verdict-icon { color: #93c5fd; }

  .verdict-text { min-width: 0; }

  .verdict-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .verdict-score {
    font-size: 0.7rem;
    font-weight: 500;
    color: #94a3b8;
    border: 1px solid #334155;
    border-radius: 9999px;
    padding: 0 0.4rem;
  }

  .verdict-detail {
    margin-top: 0.2rem;
    font-size: 0.78rem;
    line-height: 1.5;
    color: #94a3b8;
  }

  /* ── Diff ── */
  .diff-toolbar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.375rem;
  }

  .diff-legend {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.68rem;
    color: #64748b;
  }

  .legend-swatch {
    display: inline-block;
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 0.125rem;
  }
  .legend-expected { background: rgba(248, 113, 113, 0.5); }
  .legend-actual   { background: rgba(74, 222, 128, 0.5); margin-left: 0.5rem; }

  .diff-actions {
    margin-left: auto;
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
  }

  .mini-btn {
    font-size: 0.68rem;
    padding: 0.1rem 0.45rem;
    border-radius: 0.25rem;
    border: 1px solid #1e293b;
    color: #94a3b8;
    transition: all 0.15s;
  }
  .mini-btn:hover { color: #e2e8f0; border-color: #334155; }
  .mini-active { color: #bfdbfe; border-color: #1e3a8a; background: rgba(30, 58, 138, 0.3); }

  .diff {
    border: 1px solid #1e293b;
    border-radius: 0.375rem;
    overflow: auto;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.74rem;
    line-height: 1.6;
    user-select: text;
  }

  .dline {
    display: flex;
    align-items: flex-start;
    min-width: max-content;
    padding-right: 0.5rem;
  }

  .gutter {
    flex: 0 0 2.5rem;
    text-align: right;
    padding-right: 0.5rem;
    color: #475569;
    user-select: none;
  }

  .marker {
    flex: 0 0 1rem;
    text-align: center;
    user-select: none;
  }

  .dtext {
    white-space: pre;
    padding-right: 1rem;
  }

  .row-same     { color: #94a3b8; }
  .row-expected { background: rgba(127, 29, 29, 0.25); color: #fca5a5; }
  .row-actual   { background: rgba(20, 83, 45, 0.25); color: #86efac; }
  .row-note     { color: #64748b; font-style: italic; }

  .fold-row {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.15rem 0 0.15rem 3.5rem;
    color: #475569;
    background: #0f1319;
    border-top: 1px solid #1a2233;
    border-bottom: 1px solid #1a2233;
    font-size: 0.7rem;
  }
  .fold-row:hover { color: #94a3b8; }

  /* Side-by-side */
  .split-head {
    display: grid;
    grid-template-columns: 1fr 1fr;
    font-size: 0.68rem;
    color: #64748b;
    background: #0f1319;
    border-bottom: 1px solid #1e293b;
    position: sticky;
    top: 0;
  }
  .split-head span { padding: 0.2rem 0.5rem 0.2rem 3rem; }
  .split-head span + span { border-left: 1px solid #1e293b; }

  .split-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .split-cell {
    display: flex;
    align-items: flex-start;
    min-width: 0;
    overflow-x: auto;
  }
  .split-cell + .split-cell { border-left: 1px solid #1e293b; }

  .split-row.row-same    { color: #94a3b8; }
  .split-row.row-changed .split-cell:first-child { background: rgba(127, 29, 29, 0.25); color: #fca5a5; }
  .split-row.row-changed .split-cell:last-child  { background: rgba(20, 83, 45, 0.25); color: #86efac; }
  .split-row.row-missing .split-cell:first-child { background: rgba(127, 29, 29, 0.25); color: #fca5a5; }
  .split-row.row-missing .split-cell:last-child  { background: rgba(30, 41, 59, 0.5); }
  .split-row.row-extra   .split-cell:first-child { background: rgba(30, 41, 59, 0.5); }
  .split-row.row-extra   .split-cell:last-child  { background: rgba(20, 83, 45, 0.25); color: #86efac; }

  /* ── Error body ── */
  .error-headline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #fca5a5;
    background: rgba(127, 29, 29, 0.2);
    border: 1px solid #7f1d1d;
    border-radius: 0.375rem;
    padding: 0.4rem 0.6rem;
    margin-bottom: 0.5rem;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .error-body {
    white-space: pre-wrap;
    word-break: break-word;
    user-select: text;
    cursor: text;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.74rem;
    line-height: 1.55;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 0.375rem;
    padding: 0.5rem 0.6rem;
    max-height: 20rem;
    overflow: auto;
  }
</style>
