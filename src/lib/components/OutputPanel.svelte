<script lang="ts">
  /**
   * OutputPanel
   *
   * Shows run results, submission verdicts, and recent history.
   * Tabs: Output (latest run) | Submit (latest verdict) | History
   */
  import type { RunSnapshot, SubmitSnapshot } from '$lib/types/execution.js';

  interface Props {
    latestRun?: RunSnapshot | null;
    latestSubmit?: SubmitSnapshot | null;
    runs?: RunSnapshot[];
    submissions?: SubmitSnapshot[];
  }

  let {
    latestRun = null,
    latestSubmit = null,
    runs = [],
    submissions = []
  }: Props = $props();

  let activeTab = $state<'output' | 'submit' | 'history'>('output');

  function formatTime(ts: number): string {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function verdictClass(verdict: string): string {
    if (verdict === 'accepted')     return 'text-green-400';
    if (verdict === 'wrong_answer') return 'text-red-400';
    if (verdict === 'error')        return 'text-red-400';
    return 'text-slate-400';
  }
</script>

<div class="output-panel-wrap">
  <!-- Mini tab bar -->
  <div class="flex border-b border-slate-700 px-3 pt-1">
    {#each (['output', 'submit', 'history'] as const) as t}
      <button
        class="tab-btn text-xs py-1.5 px-3"
        class:active={activeTab === t}
        onclick={() => activeTab = t}
      >
        {t === 'output' ? 'Output' : t === 'submit' ? 'Submit' : 'History'}
      </button>
    {/each}
  </div>

  <div class="output-body output-panel text-slate-300">
    <!-- ── Output tab ── -->
    {#if activeTab === 'output'}
      {#if latestRun}
        <div class="flex items-center gap-3 mb-2">
          <span class="text-xs text-slate-500">{formatTime(latestRun.timestamp)}</span>
          <span class="badge" class:badge-green={latestRun.result.status === 'ok'}
                              class:badge-red={latestRun.result.status !== 'ok'}>
            {latestRun.result.status === 'ok' ? 'OK' : 'Error'}
          </span>
          {#if latestRun.result.durationMs !== null}
            <span class="text-xs text-slate-500">{latestRun.result.durationMs}ms</span>
          {/if}
        </div>
        {#if latestRun.result.stdout}
          <pre class="whitespace-pre-wrap text-green-300">{latestRun.result.stdout}</pre>
        {/if}
        {#if latestRun.result.stderr}
          <pre class="whitespace-pre-wrap text-red-400 mt-2">{latestRun.result.stderr}</pre>
        {/if}
      {:else}
        <p class="text-slate-500 italic text-sm">Click "Run" to execute your code.</p>
      {/if}
    {/if}

    <!-- ── Submit tab ── -->
    {#if activeTab === 'submit'}
      {#if latestSubmit}
        <div class="flex items-center gap-3 mb-3">
          <span class="text-xs text-slate-500">{formatTime(latestSubmit.timestamp)}</span>
          <span class="font-semibold {verdictClass(latestSubmit.result.verdict)} capitalize">
            {latestSubmit.result.verdict.replace('_', ' ')}
          </span>
          {#if latestSubmit.result.score !== null}
            <span class="badge badge-blue">Score: {latestSubmit.result.score}/100</span>
          {/if}
        </div>
        <p class="text-sm text-slate-300 mb-3">{latestSubmit.result.message}</p>
        {#if latestSubmit.result.testResults?.length}
          <div class="space-y-1">
            {#each latestSubmit.result.testResults as tr}
              <div class="flex items-center gap-2 text-xs">
                <span class={tr.passed ? 'text-green-400' : 'text-red-400'}>
                  {tr.passed ? '✓' : '✗'}
                </span>
                <span class="text-slate-400">{tr.name}</span>
                {#if tr.durationMs !== undefined}
                  <span class="text-slate-600">{tr.durationMs}ms</span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      {:else}
        <p class="text-slate-500 italic text-sm">Click "Submit" to grade your solution.</p>
      {/if}
    {/if}

    <!-- ── History tab ── -->
    {#if activeTab === 'history'}
      {#if runs.length === 0 && submissions.length === 0}
        <p class="text-slate-500 italic text-sm">No history yet.</p>
      {:else}
        <div class="space-y-2">
          <!-- Interleave runs and submissions sorted by timestamp -->
          {#each [...runs.map(r => ({ ...r, kind: 'run' as const })),
                  ...submissions.map(s => ({ ...s, kind: 'submit' as const }))]
                  .sort((a, b) => b.timestamp - a.timestamp)
                  .slice(0, 20) as entry}
            <div class="flex items-center gap-2 text-xs border-b border-slate-800 pb-1.5">
              <span class="badge" class:badge-blue={entry.kind === 'run'}
                                  class:badge-green={entry.kind === 'submit' && (entry as typeof submissions[0]).result.verdict === 'accepted'}
                                  class:badge-red={entry.kind === 'submit' && (entry as typeof submissions[0]).result.verdict !== 'accepted'}>
                {entry.kind === 'run' ? 'Run' : 'Submit'}
              </span>
              <span class="text-slate-500">{formatTime(entry.timestamp)}</span>
              <span class="text-slate-400">{entry.language}</span>
              {#if entry.kind === 'run'}
                <span class={entry.result.status === 'ok' ? 'text-green-400' : 'text-red-400'}>
                  {entry.result.status}
                </span>
              {:else}
                <span class="{verdictClass((entry as typeof submissions[0]).result.verdict)} capitalize">
                  {(entry as typeof submissions[0]).result.verdict.replace('_', ' ')}
                </span>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .output-panel-wrap {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #0d0f10;
  }

  .output-body {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem 1rem;
  }
</style>
