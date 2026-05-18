<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };

  function progressOf(slug: string): { completed: number; total: number } {
    return data.progressBySlug[slug] ?? { completed: 0, total: 0 };
  }
</script>

<Header crumbs={[{ label: 'Tracks' }]} />

<main class="flex-1 overflow-y-auto px-6 py-10 max-w-4xl mx-auto w-full">
  <h1 class="text-2xl font-bold text-slate-100 mb-1">All Tracks</h1>
  <p class="text-slate-500 text-sm mb-8">Choose a track to start practicing.</p>

  {#if data.tracks.length === 0}
    <div class="rounded-xl border border-slate-700 bg-surface-900 p-8 text-center">
      <p class="text-slate-400 mb-2">No tracks found.</p>
      <p class="text-slate-500 text-sm">
        Add a track folder to <code class="text-sky-400">courses/</code> with a
        <code class="text-sky-400">course.yaml</code> and problem subdirectories.
      </p>
    </div>
  {:else}
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
      {#each data.tracks as track}
        {@const prog = progressOf(track.slug)}
        <a
          href="/tracks/{track.slug}"
          class="group rounded-xl border border-slate-700 bg-surface-900 p-6
                 hover:border-accent-500 hover:bg-surface-800 transition-colors duration-150
                 no-underline block"
        >
          <div class="flex items-start justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-100 group-hover:text-white">
              {track.title}
            </h2>
            <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'} ml-2 flex-shrink-0">
              {track.difficulty}
            </span>
          </div>

          <p class="text-sm text-slate-400 mb-4 leading-relaxed line-clamp-2">
            {track.description}
          </p>

          {#if prog.total > 0 && prog.completed > 0}
            <div class="track-progress-bar" aria-label="track completion">
              <div class="track-progress-fill" style="width: {(prog.completed / prog.total) * 100}%"></div>
            </div>
          {/if}

          <div class="flex items-center gap-3 text-xs text-slate-500 mt-3">
            <span>
              {#if prog.total > 0 && prog.completed > 0}
                <span class="text-slate-300 font-semibold">{prog.completed}</span>
                <span class="text-slate-600">/</span>
                {prog.total} done
              {:else}
                {track.problems.length} problem{track.problems.length !== 1 ? 's' : ''}
              {/if}
            </span>
            {#if track.tags.length > 0}
              <span class="text-slate-700">·</span>
              {#each track.tags.slice(0, 3) as tag}
                <span class="text-slate-600">{tag}</span>
              {/each}
            {/if}
          </div>
        </a>
      {/each}
    </div>
  {/if}
</main>

<style>
  .track-progress-bar {
    height: 3px;
    background: #1a1f2e;
    border-radius: 999px;
    overflow: hidden;
  }
  .track-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    transition: width 600ms cubic-bezier(0.22, 1, 0.36, 1);
  }
</style>
