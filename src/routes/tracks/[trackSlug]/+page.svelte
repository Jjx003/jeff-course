<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import ProgressRing from '$lib/components/ProgressRing.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let track = $derived(data.track);
  let completions = $derived(data.completions);

  // Build a quick lookup: problemId → completion record.
  let completionMap = $derived.by(() => {
    const m = new Map<string, (typeof completions)[number]>();
    for (const c of completions) m.set(c.problemId, c);
    return m;
  });

  let completedCount = $derived(completions.filter((c) => c.completed).length);
  let totalCount = $derived(track.problems.length);
  let progress = $derived(totalCount === 0 ? 0 : completedCount / totalCount);

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };

  function isCompleted(problemSlug: string): boolean {
    return completionMap.get(`${track.slug}/${problemSlug}`)?.completed ?? false;
  }
</script>

<Header
  crumbs={[
    { label: 'Tracks', href: '/tracks' },
    { label: track.title }
  ]}
/>

<main class="flex-1 overflow-y-auto px-6 py-10 max-w-3xl mx-auto w-full">
  <!-- Track header with progress ring -->
  <div class="track-header">
    <div class="track-header-meta">
      <div class="flex items-center gap-3 mb-2">
        <h1 class="text-2xl font-bold text-slate-100">{track.title}</h1>
        <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'}">
          {track.difficulty}
        </span>
      </div>
      <p class="text-slate-400 text-sm leading-relaxed max-w-xl">{track.description}</p>
      {#if track.tags.length > 0}
        <div class="flex gap-2 mt-3 flex-wrap">
          {#each track.tags as tag}
            <span class="badge badge-blue">{tag}</span>
          {/each}
        </div>
      {/if}
    </div>

    {#if totalCount > 0}
      <div class="track-progress" title="{completedCount} of {totalCount} modules completed">
        <ProgressRing
          value={progress}
          size={84}
          stroke={7}
          label="{Math.round(progress * 100)}%"
          sublabel="Progress"
        />
      </div>
    {/if}
  </div>

  <!-- Progress bar (linear) under the header for quick visual scan -->
  {#if totalCount > 0}
    <div class="progress-strip" aria-label="track completion">
      <div class="progress-strip-bar" style="width: {progress * 100}%"></div>
    </div>
    <div class="progress-strip-label">
      {completedCount}/{totalCount} completed
    </div>
  {/if}

  <!-- Problem list -->
  <div class="space-y-3 mt-6">
    {#each track.problems as problem, idx}
      {@const done = isCompleted(problem.slug)}
      <a
        href="/tracks/{track.slug}/problems/{problem.slug}"
        class="group flex items-center gap-4 rounded-lg border px-5 py-4
               transition-colors duration-150 no-underline"
        class:row-done={done}
        class:row-default={!done}
      >
        <!-- Order number / check -->
        <span class="row-status">
          {#if done}
            <span class="check-mark" aria-label="completed">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 13l4 4L19 7" />
              </svg>
            </span>
          {:else}
            <span class="text-slate-600 text-sm font-mono">{String(idx + 1).padStart(2, '0')}</span>
          {/if}
        </span>

        <!-- Title + description -->
        <div class="flex-1 min-w-0">
          <div class="text-sm font-semibold truncate"
               class:text-slate-200={!done}
               class:text-slate-100={done}>
            {problem.title}
          </div>
          {#if problem.description}
            <div class="text-xs text-slate-500 mt-0.5 truncate">{problem.description}</div>
          {/if}
        </div>

        <!-- Metadata -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
            {problem.difficulty}
          </span>
          <span class="text-xs text-slate-600">{problem.estimatedMinutes}m</span>
          {#if problem.type === 'reading'}
            <span class="text-xs text-slate-500 font-mono uppercase tracking-wider">Read</span>
          {:else}
            {#each problem.languages as lang}
              <span class="text-xs text-slate-600 font-mono">{lang === 'cpp' ? 'C++' : 'Py'}</span>
            {/each}
          {/if}
        </div>

        <span class="text-slate-600 group-hover:text-slate-400 transition-colors">→</span>
      </a>
    {/each}
  </div>

  {#if track.problems.length === 0}
    <div class="rounded-xl border border-slate-700 bg-surface-900 p-8 text-center">
      <p class="text-slate-400">No problems in this track yet.</p>
      <p class="text-slate-500 text-sm mt-1">
        Add module directories with <code class="text-sky-400">module.yaml</code> inside
        <code class="text-sky-400">courses/{track.slug}/</code>.
      </p>
    </div>
  {/if}
</main>

<style>
  .track-header {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    margin-bottom: 1.25rem;
  }
  .track-header-meta {
    flex: 1;
    min-width: 0;
  }
  .track-progress {
    flex-shrink: 0;
  }

  .progress-strip {
    height: 4px;
    background: #1a1f2e;
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 0.25rem;
  }
  .progress-strip-bar {
    height: 100%;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    transition: width 600ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .progress-strip-label {
    font-size: 0.7rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
  }

  /* Row variants */
  .row-default {
    border-color: #334155;
    background: #16181b;
  }
  .row-default:hover {
    border-color: #60a5fa;
    background: #1a1f2e;
  }
  .row-done {
    border-color: rgba(96, 165, 250, 0.25);
    background: linear-gradient(180deg, rgba(96, 165, 250, 0.05), #16181b);
  }
  .row-done:hover {
    border-color: rgba(96, 165, 250, 0.5);
  }

  .row-status {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    flex-shrink: 0;
  }
  .check-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 999px;
    background: rgba(96, 165, 250, 0.18);
    color: #60a5fa;
  }
</style>
