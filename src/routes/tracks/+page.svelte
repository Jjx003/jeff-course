<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner: 'badge-green',
    intermediate: 'badge-yellow',
    advanced: 'badge-red'
  };

  function progressOf(slug: string): { completed: number; total: number } {
    return data.progressBySlug[slug] ?? { completed: 0, total: 0 };
  }

  function progressRatio(slug: string): number {
    const progress = progressOf(slug);
    return progress.total === 0 ? 0 : progress.completed / progress.total;
  }

  function actionLabel(slug: string): string {
    const progress = progressOf(slug);
    if (progress.total > 0 && progress.completed === progress.total) return 'Review';
    return progress.completed > 0 ? 'Continue' : 'Start';
  }

  function trackMinutes(track: PageData['tracks'][number]): number {
    return track.problems.reduce((sum, problem) => sum + problem.estimatedMinutes, 0);
  }

  let totalModules = $derived(data.tracks.reduce((sum, track) => sum + track.problems.length, 0));
  let startedTracks = $derived(data.tracks.filter((track) => progressOf(track.slug).completed > 0).length);
</script>

<Header crumbs={[{ label: 'Tracks' }]} />

<main class="flex-1 overflow-y-auto px-6 py-10 max-w-5xl mx-auto w-full">
  <div class="tracks-heading">
    <div>
      <h1 class="text-2xl font-bold text-slate-100 mb-1">All Tracks</h1>
      <p class="text-slate-500 text-sm">Choose a track to start practicing.</p>
    </div>
    {#if data.tracks.length > 0}
      <div class="tracks-summary" aria-label="Course library summary">
        <span><strong>{data.tracks.length}</strong> tracks</span>
        <span><strong>{totalModules}</strong> modules</span>
        <span><strong>{startedTracks}</strong> started</span>
      </div>
    {/if}
  </div>

  {#if data.tracks.length === 0}
    <div class="rounded-xl border border-slate-700 bg-surface-900 p-8 text-center">
      <p class="text-slate-400 mb-2">No tracks found.</p>
      <p class="text-slate-500 text-sm">
        Add a track folder to <code class="text-sky-400">courses/</code> with a
        <code class="text-sky-400">course.yaml</code> and problem subdirectories.
      </p>
    </div>
  {:else}
    <div class="track-grid">
      {#each data.tracks as track}
        {@const prog = progressOf(track.slug)}
        {@const ratio = progressRatio(track.slug)}
        {@const minutes = trackMinutes(track)}
        <a href="/tracks/{track.slug}" class="track-card group">
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

          <div class="track-progress-bar" aria-label="track completion">
            <div class="track-progress-fill" style="width: {ratio * 100}%"></div>
          </div>

          <div class="track-card-footer">
            <span>
              {#if prog.total > 0}
                <span class="text-slate-300 font-semibold">{prog.completed}</span>
                <span class="text-slate-600">/</span>
                {prog.total} done
              {:else}
                {track.problems.length} module{track.problems.length !== 1 ? 's' : ''}
              {/if}
            </span>
            <span class="text-slate-700">/</span>
            <span>{Math.round((minutes / 60) * 10) / 10}h</span>
            {#if track.tags.length > 0}
              <span class="text-slate-700">/</span>
              {#each track.tags.slice(0, 3) as tag}
                <span class="text-slate-600">{tag}</span>
              {/each}
            {/if}
            <span class="track-action">{actionLabel(track.slug)}</span>
          </div>
        </a>
      {/each}
    </div>
  {/if}
</main>

<style>
  .tracks-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .tracks-summary {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.75rem;
    flex-wrap: wrap;
    color: #94a3b8;
    font-size: 0.78rem;
  }

  .tracks-summary span {
    display: inline-flex;
    align-items: baseline;
    gap: 0.25rem;
    padding: 0.35rem 0.55rem;
    border: 1px solid #1e293b;
    border-radius: 999px;
    background: #111827;
  }

  .tracks-summary strong {
    color: #f8fafc;
    font-variant-numeric: tabular-nums;
  }

  .track-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.25rem;
  }

  .track-card {
    display: flex;
    min-height: 220px;
    flex-direction: column;
    padding: 1.5rem;
    border: 1px solid #334155;
    border-radius: 10px;
    background: #16181b;
    color: inherit;
    text-decoration: none;
    transition: border-color 150ms ease, background 150ms ease, transform 150ms ease;
  }

  .track-card:hover {
    border-color: #60a5fa;
    background: #1a1f2e;
    transform: translateY(-1px);
  }

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

  .track-card-footer {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    flex-wrap: wrap;
    margin-top: auto;
    padding-top: 0.9rem;
    color: #64748b;
    font-size: 0.75rem;
  }

  .track-action {
    margin-left: auto;
    padding: 0.32rem 0.6rem;
    border: 1px solid rgba(96, 165, 250, 0.35);
    border-radius: 999px;
    color: #bfdbfe;
    font-weight: 700;
  }

  @media (max-width: 760px) {
    .tracks-heading {
      flex-direction: column;
    }

    .tracks-summary {
      justify-content: flex-start;
    }

    .track-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
