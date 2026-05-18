<script lang="ts">
  /**
   * Sessions dashboard.
   *
   * Lists every sandbox session ever started, most recent first, and lets
   * the user cancel/kill running ones or expand a row to tail the live
   * stdout/stderr stream over SSE.
   *
   * Polling strategy:
   *   - GET /api/sessions?limit=100 every 2s. Merged by id so an expanded
   *     drawer doesn't lose its place when the response order shifts.
   *   - A 1s "clock" tick drives live duration math without thrashing
   *     fetches.
   */

  import { onDestroy, onMount } from 'svelte';
  import { browser } from '$app/environment';

  import Header from '$lib/components/Header.svelte';
  import type {
    LogChunk,
    SandboxCapabilities,
    SessionRecord,
    SessionStatus
  } from '$lib/types/sandbox.js';
  import { isTerminalStatus } from '$lib/types/sandbox.js';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const POLL_MS = 2_000;
  const CLOCK_MS = 1_000;

  // We snapshot `data.initial` into a local `$state` array so polling can
  // mutate it in place. SvelteKit only re-runs the load function on a
  // navigation, so capturing the initial value here is intentional.
  const initialSessions: SessionRecord[] = data.initial ?? [];
  let sessions = $state<SessionRecord[]>(initialSessions);
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let clockTimer: ReturnType<typeof setInterval> | null = null;
  let clock = $state(Date.now());
  let services: typeof import('$lib/services/index.js') | null = null;
  let capabilities = $state<SandboxCapabilities | null>(null);
  let bulkBusy = $state(false);
  let lastRefreshError = $state<string | null>(null);

  // ── Expanded-drawer state ─────────────────────────────────────────────
  //
  // expanded[id] === true ⇒ the detail drawer is visible.
  // We track live stdout/stderr per id so collapsing + re-expanding doesn't
  // drop the buffer for a session that's still running. Subscriptions are
  // keyed by id and stored alongside the buffers.

  let expanded = $state<Record<string, boolean>>({});
  let liveStdout = $state<Record<string, string>>({});
  let liveStderr = $state<Record<string, string>>({});
  const subscriptions = new Map<string, () => void>();

  // ── Refresh / poll ────────────────────────────────────────────────────

  let inflight = $state(false);

  async function refresh() {
    if (inflight) return;
    inflight = true;
    try {
      const res = await fetch('/api/sessions?limit=100');
      if (!res.ok) {
        lastRefreshError = `${res.status}: ${res.statusText}`;
        return;
      }
      const next = (await res.json()) as SessionRecord[];
      sessions = mergeById(sessions, next);
      lastRefreshError = null;
    } catch (err) {
      lastRefreshError = err instanceof Error ? err.message : String(err);
    } finally {
      inflight = false;
    }
  }

  /**
   * Merge an incoming sessions list with the current state by id. We keep
   * the server's order (most recent first) but swap in fresh field values
   * from `next`. Rows that have disappeared from the server (e.g. retained
   * limit shifted past them) are dropped.
   */
  function mergeById(prev: SessionRecord[], next: SessionRecord[]): SessionRecord[] {
    const prevById = new Map(prev.map((s) => [s.id, s]));
    return next.map((n) => ({ ...(prevById.get(n.id) ?? n), ...n }));
  }

  // ── Drawer toggle ─────────────────────────────────────────────────────

  function toggleExpanded(id: string) {
    if (expanded[id]) collapseRow(id);
    else expandRow(id);
  }

  function expandRow(id: string) {
    expanded[id] = true;
    if (!liveStdout[id]) liveStdout[id] = '';
    if (!liveStderr[id]) liveStderr[id] = '';
    if (!services) return;

    if (subscriptions.has(id)) return;
    const unsub = services.sessionsService.subscribe(id, (chunk: LogChunk) => {
      if (chunk.kind === 'stdout') {
        liveStdout[id] = (liveStdout[id] ?? '') + chunk.data;
      } else if (chunk.kind === 'stderr') {
        liveStderr[id] = (liveStderr[id] ?? '') + chunk.data;
      } else if (chunk.kind === 'exit') {
        const sub = subscriptions.get(id);
        if (sub) {
          sub();
          subscriptions.delete(id);
        }
      }
    });
    subscriptions.set(id, unsub);
  }

  function collapseRow(id: string) {
    expanded[id] = false;
    const sub = subscriptions.get(id);
    if (sub) {
      sub();
      subscriptions.delete(id);
    }
  }

  // ── Per-row actions ───────────────────────────────────────────────────

  async function cancelOne(id: string) {
    if (!services) return;
    await services.sessionsService.cancel(id);
    void refresh();
  }

  async function killOne(id: string) {
    if (!services) return;
    await services.sessionsService.kill(id);
    void refresh();
  }

  async function cancelAllActive() {
    if (!services || bulkBusy) return;
    bulkBusy = true;
    try {
      const targets = sessions.filter((s) => isActive(s.status));
      await Promise.all(targets.map((s) => services!.sessionsService.cancel(s.id)));
      await refresh();
    } finally {
      bulkBusy = false;
    }
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────

  onMount(async () => {
    if (!browser) return;
    services = await import('$lib/services/index.js');
    void refresh();
    try {
      capabilities = await services.sessionsService.capabilities();
    } catch {
      capabilities = null;
    }
    pollTimer = setInterval(refresh, POLL_MS);
    clockTimer = setInterval(() => { clock = Date.now(); }, CLOCK_MS);
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
    if (clockTimer) clearInterval(clockTimer);
    for (const unsub of subscriptions.values()) {
      try { unsub(); } catch { /* ignore */ }
    }
    subscriptions.clear();
  });

  // ── Helpers ───────────────────────────────────────────────────────────

  function isActive(s: SessionStatus): boolean {
    return s === 'queued' || s === 'starting' || s === 'running';
  }

  function isCancellable(s: SessionStatus): boolean {
    return s === 'queued' || s === 'starting' || s === 'running';
  }

  function isKillable(s: SessionStatus): boolean {
    return s === 'starting' || s === 'running';
  }

  function shortId(id: string): string {
    return id.slice(0, 8);
  }

  function parseProblem(problemId: string): { trackSlug: string; problemSlug: string } | null {
    const [trackSlug, problemSlug] = problemId.split('/');
    if (!trackSlug || !problemSlug) return null;
    return { trackSlug, problemSlug };
  }

  function relativeTime(ts: number, now: number): string {
    const diffSec = Math.max(0, Math.floor((now - ts) / 1000));
    if (diffSec < 5) return 'just now';
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return new Date(ts).toLocaleDateString();
  }

  function formatDuration(ms: number): string {
    if (ms < 0) ms = 0;
    if (ms < 1000) return `${ms}ms`;
    const sec = ms / 1000;
    if (sec < 60) return `${sec.toFixed(1)}s`;
    const minutes = Math.floor(sec / 60);
    const remSec = Math.floor(sec - minutes * 60);
    if (minutes < 60) return `${minutes}m ${remSec}s`;
    const hours = Math.floor(minutes / 60);
    const remMin = minutes - hours * 60;
    return `${hours}h ${remMin}m`;
  }

  function durationFor(s: SessionRecord, now: number): string {
    if (isTerminalStatus(s.status) && s.completedAt) {
      return formatDuration(s.completedAt - s.startedAt);
    }
    if (isActive(s.status)) {
      return formatDuration(now - s.startedAt);
    }
    return '—';
  }

  function gpuLabel(gpu: SessionRecord['resources']['gpu']): string {
    if (gpu === 'none') return 'no gpu';
    if (gpu === 'all') return 'gpu';
    return `gpu#${gpu.device}`;
  }

  function resourcesSummary(s: SessionRecord): string {
    const { memoryMb, cpus, gpu, timeoutMs } = s.resources;
    const mem = memoryMb > 0 ? `${memoryMb} MB` : 'mem—';
    const cpu = cpus > 0 ? `${cpus} cpu` : 'cpu—';
    const to = timeoutMs ? `${Math.round(timeoutMs / 1000)}s` : '';
    const parts = [mem, cpu, gpuLabel(gpu)];
    if (to) parts.push(to);
    return parts.join(' / ');
  }

  function modeLabel(mode: SessionRecord['mode']): string {
    if (mode === 'baremetal') return 'Baremetal';
    if (mode === 'docker') return 'Container';
    if (mode === 'docker-gpu') return 'Container + GPU';
    return mode;
  }

  function modeBadgeClass(mode: SessionRecord['mode']): string {
    if (mode === 'baremetal') return 'badge-slate';
    if (mode === 'docker') return 'badge-blue';
    if (mode === 'docker-gpu') return 'badge-purple';
    return 'badge-slate';
  }

  function statusBadgeClass(status: SessionStatus): string {
    switch (status) {
      case 'queued':    return 'badge-status-queued';
      case 'starting':  return 'badge-status-starting';
      case 'running':   return 'badge-status-running';
      case 'completed': return 'badge-status-completed';
      case 'cancelled': return 'badge-status-cancelled';
      case 'killed':    return 'badge-status-killed';
      case 'failed':    return 'badge-status-failed';
      case 'crashed':   return 'badge-status-failed';
      default:          return 'badge-status-cancelled';
    }
  }

  function statusLabel(status: SessionStatus): string {
    switch (status) {
      case 'completed': return 'completed';
      case 'cancelled': return 'cancelled';
      case 'killed':    return 'killed';
      case 'failed':    return 'failed';
      case 'crashed':   return 'crashed';
      case 'queued':    return 'queued';
      case 'starting':  return 'starting';
      case 'running':   return 'running';
      default:          return status;
    }
  }

  function verdictClass(verdict: string | null | undefined): string {
    if (verdict === 'accepted')     return 'text-green-400';
    if (verdict === 'wrong_answer') return 'text-red-400';
    if (verdict === 'error')        return 'text-red-400';
    if (verdict === 'pending')      return 'text-slate-400';
    return 'text-slate-500';
  }

  // ── Derived ───────────────────────────────────────────────────────────

  let activeCount = $derived(sessions.filter((s) => isActive(s.status)).length);
  let capabilityBanner = $derived.by(() => {
    if (!capabilities) return null;
    if (!capabilities.docker.available) {
      return {
        tone: 'warn' as const,
        text: `Container runtime not detected${capabilities.docker.reason ? ' — ' + capabilities.docker.reason : ''}. Baremetal mode only.`
      };
    }
    if (capabilities.gpu.available) {
      return {
        tone: 'good' as const,
        text: `Docker ${capabilities.docker.version ?? 'available'} · GPU passthrough OK (${capabilities.gpu.deviceCount ?? 1} device${(capabilities.gpu.deviceCount ?? 1) === 1 ? '' : 's'}).`
      };
    }
    return {
      tone: 'neutral' as const,
      text: `Docker ${capabilities.docker.version ?? 'available'} · CPU containers only${capabilities.gpu.reason ? ' (' + capabilities.gpu.reason + ')' : ''}.`
    };
  });
</script>

<div class="page-shell">
  <Header crumbs={[{ label: 'Sessions' }]} />

  <main class="page-body">
    {#if capabilityBanner}
      <div class="banner banner-{capabilityBanner.tone}">{capabilityBanner.text}</div>
    {/if}

    {#if lastRefreshError}
      <div class="banner banner-warn">Refresh failed: {lastRefreshError}</div>
    {/if}

    <div class="toolbar">
      <div class="toolbar-info">
        <strong>{sessions.length}</strong>
        <span class="text-slate-500">session{sessions.length === 1 ? '' : 's'}</span>
        <span class="text-slate-700">·</span>
        <strong class={activeCount > 0 ? 'text-blue-400' : 'text-slate-500'}>{activeCount}</strong>
        <span class="text-slate-500">active</span>
      </div>
      <div class="toolbar-actions">
        <button
          class="btn-ghost text-xs"
          onclick={() => void refresh()}
          disabled={inflight}
          title="Refresh now"
        >
          Refresh now
        </button>
        <button
          class="btn-ghost text-xs"
          onclick={() => void cancelAllActive()}
          disabled={bulkBusy || activeCount === 0}
          title="Cancel every running or queued session"
        >
          Cancel all active
        </button>
      </div>
    </div>

    {#if sessions.length === 0}
      <p class="empty">No sandbox sessions yet. Click Run or Submit on a problem to create one.</p>
    {:else}
      <div class="table-wrap">
        <table class="sessions-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Problem</th>
              <th>Action</th>
              <th>Mode</th>
              <th>Status</th>
              <th>Started</th>
              <th>Duration</th>
              <th>Resources</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each sessions as s (s.id)}
              {@const problem = parseProblem(s.problemId)}
              <tr class="row" class:row-expanded={expanded[s.id]}>
                <td>
                  <button
                    class="id-btn"
                    onclick={() => toggleExpanded(s.id)}
                    title={s.id}
                  >
                    <span class="caret">{expanded[s.id] ? '▾' : '▸'}</span>
                    <code>{shortId(s.id)}</code>
                  </button>
                </td>
                <td>
                  {#if problem}
                    <a
                      class="problem-link"
                      href={`/tracks/${problem.trackSlug}/problems/${problem.problemSlug}`}
                      title={s.problemId}
                    >
                      {problem.problemSlug}
                    </a>
                    <div class="text-slate-600 text-[0.65rem]">{problem.trackSlug}</div>
                  {:else}
                    <code class="text-slate-500">{s.problemId}</code>
                  {/if}
                </td>
                <td>
                  <span class="badge badge-slate text-[0.65rem] uppercase">{s.action}</span>
                  <span class="text-slate-500 text-xs ml-1">{s.language}</span>
                </td>
                <td>
                  <span class="badge {modeBadgeClass(s.mode)}">{modeLabel(s.mode)}</span>
                </td>
                <td>
                  <span class="badge {statusBadgeClass(s.status)}">
                    {#if !isTerminalStatus(s.status)}
                      <span class="status-dot"></span>
                    {/if}
                    {statusLabel(s.status)}
                  </span>
                </td>
                <td class="text-slate-400 text-xs">{relativeTime(s.startedAt, clock)}</td>
                <td class="text-slate-400 text-xs tabular">{durationFor(s, clock)}</td>
                <td class="text-slate-500 text-xs tabular">{resourcesSummary(s)}</td>
                <td class="actions-cell">
                  {#if isCancellable(s.status)}
                    <button class="btn-action btn-cancel" onclick={() => void cancelOne(s.id)}>Cancel</button>
                  {/if}
                  {#if isKillable(s.status)}
                    <button class="btn-action btn-kill" onclick={() => void killOne(s.id)}>Kill</button>
                  {/if}
                  <button class="btn-action btn-detail" onclick={() => toggleExpanded(s.id)}>
                    {expanded[s.id] ? 'Hide' : 'Details'}
                  </button>
                </td>
              </tr>
              {#if expanded[s.id]}
                <tr class="drawer">
                  <td colspan="9">
                    <div class="drawer-body">
                      <div class="drawer-meta">
                        <div><span class="meta-label">ID</span> <code>{s.id}</code></div>
                        <div><span class="meta-label">Problem</span> <code>{s.problemId}</code></div>
                        <div><span class="meta-label">Language</span> {s.language}</div>
                        <div><span class="meta-label">Action</span> {s.action}</div>
                        <div><span class="meta-label">Mode</span> {modeLabel(s.mode)}</div>
                        <div><span class="meta-label">Status</span> {statusLabel(s.status)}</div>
                        <div><span class="meta-label">Memory</span> {s.resources.memoryMb > 0 ? `${s.resources.memoryMb} MB` : 'unlimited'}</div>
                        <div><span class="meta-label">CPUs</span> {s.resources.cpus > 0 ? s.resources.cpus : 'unlimited'}</div>
                        <div><span class="meta-label">GPU</span> {gpuLabel(s.resources.gpu)}</div>
                        <div><span class="meta-label">Timeout</span> {Math.round(s.resources.timeoutMs / 1000)}s</div>
                        <div><span class="meta-label">Started</span> {new Date(s.startedAt).toLocaleString()}</div>
                        <div>
                          <span class="meta-label">Completed</span>
                          {s.completedAt ? new Date(s.completedAt).toLocaleString() : '—'}
                        </div>
                        <div><span class="meta-label">Exit code</span> {s.exitCode ?? '—'}</div>
                        {#if s.hostPid !== null}
                          <div><span class="meta-label">Host PID</span> {s.hostPid}</div>
                        {/if}
                        {#if s.containerName}
                          <div><span class="meta-label">Container</span> <code>{s.containerName}</code></div>
                        {/if}
                        <div><span class="meta-label">Stdout bytes</span> {s.stdoutBytes}</div>
                        <div><span class="meta-label">Stderr bytes</span> {s.stderrBytes}</div>
                        {#if s.errorMessage}
                          <div class="col-span-full"><span class="meta-label">Error</span> <span class="text-red-400">{s.errorMessage}</span></div>
                        {/if}
                        {#if s.action === 'submit' && s.submitVerdict}
                          <div class="col-span-full">
                            <span class="meta-label">Verdict</span>
                            <span class={verdictClass(s.submitVerdict)}>{s.submitVerdict.replace('_', ' ')}</span>
                            {#if s.submitScore !== null && s.submitScore !== undefined}
                              <span class="ml-2 text-slate-500">Score: {s.submitScore}/100</span>
                            {/if}
                          </div>
                          {#if s.submitMessage}
                            <div class="col-span-full">
                              <span class="meta-label">Message</span>
                              <span class="text-slate-300 whitespace-pre-wrap">{s.submitMessage}</span>
                            </div>
                          {/if}
                        {/if}
                      </div>

                      <div class="drawer-streams">
                        <div class="stream-block">
                          <div class="stream-label">stdout</div>
                          <pre class="stream stdout">{liveStdout[s.id] ?? ''}</pre>
                        </div>
                        <div class="stream-block">
                          <div class="stream-label">stderr</div>
                          <pre class="stream stderr">{liveStderr[s.id] ?? ''}</pre>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </main>
</div>

<style>
  .page-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .page-body {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem 2rem 2rem;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
  }

  .banner {
    padding: 0.6rem 0.9rem;
    border-radius: 6px;
    font-size: 0.8rem;
    margin-bottom: 0.85rem;
    border: 1px solid transparent;
  }
  .banner-warn   { background: #422006; color: #fde68a; border-color: #b45309; }
  .banner-good   { background: #052e1a; color: #bbf7d0; border-color: #16a34a; }
  .banner-neutral{ background: #131b2d; color: #cbd5e1; border-color: #2e588f; }

  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #1e293b;
  }
  .toolbar-info {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: #cbd5e1;
    font-size: 0.85rem;
  }
  .toolbar-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .empty {
    color: #64748b;
    font-style: italic;
    padding: 2rem 0;
    text-align: center;
  }

  .table-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #1e293b;
    border-radius: 8px;
    background: #0d1117;
  }

  .sessions-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
  }
  .sessions-table thead th {
    text-align: left;
    padding: 0.5rem 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    border-bottom: 1px solid #1e293b;
    text-transform: uppercase;
    font-size: 0.65rem;
    letter-spacing: 0.05em;
    background: #131b2d;
    position: sticky;
    top: 0;
    z-index: 1;
  }
  .sessions-table thead th.text-right { text-align: right; }
  .sessions-table tbody td {
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid #1a2436;
    vertical-align: middle;
  }
  .row:hover td {
    background: #131b2d;
  }
  .row-expanded td {
    background: #131b2d;
  }
  .tabular {
    font-variant-numeric: tabular-nums;
  }

  .id-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: transparent;
    border: none;
    color: #cbd5e1;
    cursor: pointer;
    padding: 0;
  }
  .id-btn:hover { color: #f1f5f9; }
  .id-btn code  {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    color: #93c5fd;
    font-size: 0.75rem;
  }
  .caret {
    width: 0.85rem;
    color: #64748b;
    font-size: 0.7rem;
  }

  .problem-link {
    color: #cbd5e1;
    text-decoration: none;
    font-weight: 500;
  }
  .problem-link:hover {
    color: #60a5fa;
    text-decoration: underline;
  }

  .actions-cell {
    display: flex;
    justify-content: flex-end;
    gap: 0.35rem;
    flex-wrap: wrap;
  }

  .btn-action {
    padding: 0.2rem 0.55rem;
    font-size: 0.7rem;
    border-radius: 4px;
    border: 1px solid #334155;
    background: #131b2d;
    color: #cbd5e1;
    cursor: pointer;
    transition: background 0.1s, border-color 0.1s, color 0.1s;
  }
  .btn-action:hover {
    background: #1e293b;
    color: #f1f5f9;
  }
  .btn-cancel:hover { border-color: #f59e0b; color: #fbbf24; }
  .btn-kill:hover   { border-color: #f87171; color: #fca5a5; }
  .btn-detail:hover { border-color: #60a5fa; color: #93c5fd; }

  /* ── Mode badges ── */
  :global(.badge-slate) {
    background: #1e293b;
    color: #cbd5e1;
  }
  :global(.badge-purple) {
    background: rgba(147, 51, 234, 0.25);
    color: #d8b4fe;
  }

  /* ── Status badges ── */
  :global(.badge-status-queued) {
    background: rgba(59, 130, 246, 0.20);
    color: #93c5fd;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  :global(.badge-status-starting) {
    background: rgba(99, 102, 241, 0.20);
    color: #a5b4fc;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  :global(.badge-status-running) {
    background: rgba(34, 197, 94, 0.20);
    color: #86efac;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  :global(.badge-status-completed) {
    background: rgba(34, 197, 94, 0.20);
    color: #4ade80;
  }
  :global(.badge-status-cancelled) {
    background: rgba(100, 116, 139, 0.30);
    color: #cbd5e1;
  }
  :global(.badge-status-killed) {
    background: rgba(249, 115, 22, 0.20);
    color: #fdba74;
  }
  :global(.badge-status-failed) {
    background: rgba(239, 68, 68, 0.20);
    color: #fca5a5;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 0 0 currentColor;
    animation: status-pulse 1.4s ease-out infinite;
  }
  @keyframes status-pulse {
    0%   { box-shadow: 0 0 0 0   currentColor; opacity: 1; }
    70%  { box-shadow: 0 0 0 6px transparent; opacity: 0.65; }
    100% { box-shadow: 0 0 0 0   transparent; opacity: 1; }
  }

  /* ── Drawer ── */
  .drawer td {
    background: #0a1322;
    padding: 0;
    border-bottom: 1px solid #1a2436;
  }
  .drawer-body {
    padding: 0.85rem 1rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }
  .drawer-meta {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.4rem 1rem;
    font-size: 0.75rem;
    color: #cbd5e1;
  }
  .drawer-meta .col-span-full { grid-column: 1 / -1; }
  .meta-label {
    color: #64748b;
    text-transform: uppercase;
    font-size: 0.62rem;
    letter-spacing: 0.06em;
    margin-right: 0.45rem;
  }

  .drawer-streams {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
  }
  @media (max-width: 900px) {
    .drawer-streams { grid-template-columns: 1fr; }
  }
  .stream-block {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .stream-label {
    font-size: 0.65rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
  }
  .stream {
    background: #050810;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.55rem 0.7rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.72rem;
    line-height: 1.45;
    color: #cbd5e1;
    max-height: 280px;
    min-height: 60px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .stream.stdout { color: #bbf7d0; }
  .stream.stderr { color: #fca5a5; }
</style>
