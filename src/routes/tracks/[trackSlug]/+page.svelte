<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let track = $derived(data.track);

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };
</script>

<Header
  crumbs={[
    { label: 'Tracks', href: '/tracks' },
    { label: track.title }
  ]}
/>

<main class="flex-1 overflow-y-auto px-6 py-10 max-w-3xl mx-auto w-full">
  <!-- Track header -->
  <div class="mb-8">
    <div class="flex items-center gap-3 mb-2">
      <h1 class="text-2xl font-bold text-slate-100">{track.title}</h1>
      <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'}">
        {track.difficulty}
      </span>
    </div>
    <p class="text-slate-400 text-sm leading-relaxed max-w-xl">{track.description}</p>
    {#if track.tags.length > 0}
      <div class="flex gap-2 mt-3">
        {#each track.tags as tag}
          <span class="badge badge-blue">{tag}</span>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Problem list -->
  <div class="space-y-3">
    {#each track.problems as problem, idx}
      <a
        href="/tracks/{track.slug}/problems/{problem.slug}"
        class="group flex items-center gap-4 rounded-lg border border-slate-700
               bg-surface-900 px-5 py-4 hover:border-accent-500 hover:bg-surface-800
               transition-colors duration-150 no-underline"
      >
        <!-- Order number -->
        <span class="text-slate-600 text-sm font-mono w-6 text-center flex-shrink-0">
          {String(idx + 1).padStart(2, '0')}
        </span>

        <!-- Title + description -->
        <div class="flex-1 min-w-0">
          <div class="text-sm font-semibold text-slate-200 group-hover:text-white truncate">
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
