<script lang="ts">
  /**
   * OutputPanel
   *
   * Shows run output and latest submission verdict.
   * Tabs: Output (latest run) | Submit (latest verdict)
   *
   * Submission history is surfaced in the toolbar dropdown, not here.
   */
  import type { RunSnapshot, SubmitSnapshot } from '$lib/types/execution.js';

  interface Props {
    latestRun?: RunSnapshot | null;
    latestSubmit?: SubmitSnapshot | null;
  }

  let { latestRun = null, latestSubmit = null }: Props = $props();

  let activeTab = $state<'output' | 'submit'>('output');
  let copied = $state(false);

  function formatTime(ts: number): string {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function verdictClass(verdict: string): string {
    if (verdict === 'accepted')     return 'text-green-400';
    if (verdict === 'wrong_answer') return 'text-red-400';
    if (verdict === 'error')        return 'text-red-400';
    return 'text-slate-400';
  }

  function getOutputText(): string {
    if (activeTab === 'output' && latestRun) {
      return [latestRun.result.stdout, latestRun.result.stderr].filter(Boolean).join('\n');
    }
    if (activeTab === 'submit' && latestSubmit) {
      const parts: string[] = [latestSubmit.result.message];
      if (latestSubmit.result.testResults?.length) {
        for (const tr of latestSubmit.result.testResults) {
          parts.push(`${tr.passed ? '✓' : '✗'} ${tr.name}`);
        }
      }
      return parts.filter(Boolean).join('\n');
    }
    return '';
  }

  async function handleCopy() {
    const text = getOutputText();
    if (!text) return;
    await navigator.clipboard.writeText(text);
    copied = true;
    setTimeout(() => { copied = false; }, 1500);
  }
</script>

<div class="output-panel-wrap">
  <div class="flex items-center border-b border-slate-700 px-3 pt-1">
    {#each (['output', 'submit'] as const) as t}
      <button
        class="tab-btn text-xs py-1.5 px-3"
        class:active={activeTab === t}
        onclick={() => activeTab = t}
      >
        {t === 'output' ? 'Output' : 'Submit'}
      </button>
    {/each}
    <button
      class="ml-auto mb-1 px-2 py-0.5 text-xs rounded text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors disabled:opacity-30"
      onclick={handleCopy}
      disabled={!getOutputText()}
      title="Copy output"
    >
      {copied ? '✓ Copied' : 'Copy'}
    </button>
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
          <pre class="output-text text-green-300">{latestRun.result.stdout}</pre>
        {/if}
        {#if latestRun.result.stderr}
          <pre class="output-text text-red-400 mt-2">{latestRun.result.stderr}</pre>
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

  .output-text {
    white-space: pre-wrap;
    user-select: text;
    cursor: text;
  }
</style>
