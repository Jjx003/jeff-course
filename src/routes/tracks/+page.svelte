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

  function trackMinutes(track: PageData['enrolledTracks'][number]): number {
    return track.problems.reduce((sum, problem) => sum + problem.estimatedMinutes, 0);
  }

  function hoursLabel(track: PageData['enrolledTracks'][number]): string {
    const hours = trackMinutes(track) / 60;
    return `${Math.round(hours * 10) / 10}h`;
  }

  function confirmPause(event: SubmitEvent, title: string): void {
    if (!confirm(`Pause ${title}? It will leave My courses, but your progress and work will be kept.`)) {
      event.preventDefault();
    }
  }
</script>

<Header crumbs={[{ label: 'Courses' }]} />

<main class="tracks-main">
  <section class="library-header">
    <div>
      <p class="kicker">Your learning</p>
      <h1>My courses</h1>
      <p>Keep the courses you are actively studying close at hand.</p>
    </div>
    <a href="#discover" class="browse-link">Discover courses</a>
  </section>

  {#if data.enrolledTracks.length === 0}
    <section class="empty-state">
      <span class="empty-mark" aria-hidden="true">+</span>
      <div>
        <h2>Your course list is empty</h2>
        <p>Enroll in one course to begin. You can preview every syllabus first.</p>
      </div>
      <a href="#discover" class="btn-primary">Browse courses</a>
    </section>
  {:else}
    <section class="enrolled-grid" aria-label="Enrolled courses">
      {#each data.enrolledTracks as track}
        {@const progress = progressOf(track.slug)}
        {@const ratio = progress.total === 0 ? 0 : progress.completed / progress.total}
        <article class="course-card">
          <a href="/tracks/{track.slug}" class="course-card-link">
            <div class="card-topline">
              <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'}">{track.difficulty}</span>
              <span>{progress.completed} / {progress.total} modules</span>
            </div>
            <h2>{track.title}</h2>
            <p>{track.description}</p>
            <div class="progress-track" aria-label="{Math.round(ratio * 100)}% complete">
              <span style="width: {ratio * 100}%"></span>
            </div>
          </a>
          <div class="card-footer">
            <div class="card-footer-meta">
              <span>{hoursLabel(track)} total</span>
              <form method="POST" action="?/unenroll" onsubmit={(event) => confirmPause(event, track.title)}>
                <input type="hidden" name="trackSlug" value={track.slug} />
                <button class="pause-button" type="submit">Pause</button>
              </form>
            </div>
            <a href="/tracks/{track.slug}" class="course-action">
              {progress.completed > 0 ? 'Continue' : 'Start course'} <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
        </article>
      {/each}
    </section>
  {/if}

  <section class="discover" id="discover">
    <div class="discover-heading">
      <div>
        <p class="kicker">Course catalog</p>
        <h2>Discover</h2>
      </div>
      <span>{data.availableTracks.length} available</span>
    </div>

    {#if data.availableTracks.length === 0}
      <p class="catalog-empty">You are enrolled in every available course.</p>
    {:else}
      <div class="catalog-list">
        {#each data.availableTracks as track}
          <article class="catalog-row">
            <a href="/tracks/{track.slug}" class="catalog-copy">
              <div class="catalog-title">
                <h3>{track.title}</h3>
                <span class="badge {DIFFICULTY_BADGE[track.difficulty] ?? 'badge-blue'}">{track.difficulty}</span>
              </div>
              <p>{track.description}</p>
              <div class="catalog-meta">
                <span>{track.problems.length} modules</span>
                <span>{hoursLabel(track)}</span>
                {#each track.tags.slice(0, 2) as tag}<span>{tag}</span>{/each}
              </div>
            </a>
            <form method="POST" action="?/enroll">
              <input type="hidden" name="trackSlug" value={track.slug} />
              <button class="enroll-button" type="submit">
                {progressOf(track.slug).completed > 0 ? 'Resume' : 'Enroll'}
              </button>
            </form>
          </article>
        {/each}
      </div>
    {/if}
  </section>
</main>

<style>
  .tracks-main { flex: 1; width: 100%; max-width: 1080px; margin: 0 auto; padding: 3rem 1.5rem 5rem; overflow-y: auto; }
  .library-header, .discover-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 1.5rem; }
  .library-header { margin-bottom: 1.6rem; }
  .kicker { margin: 0 0 0.45rem; color: #60a5fa; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.1em; text-transform: uppercase; }
  h1, .discover-heading h2 { margin: 0; color: #f8fafc; letter-spacing: -0.04em; }
  h1 { font-size: clamp(2rem, 4vw, 2.8rem); }
  .library-header p:last-child { margin: 0.6rem 0 0; color: #94a3b8; font-size: 0.9rem; }
  .browse-link { padding: 0.55rem 0.8rem; border: 1px solid #334155; border-radius: 8px; color: #cbd5e1; font-size: 0.78rem; font-weight: 650; text-decoration: none; }
  .empty-state { display: flex; align-items: center; gap: 1rem; padding: 1.4rem; border: 1px dashed #334155; border-radius: 13px; background: rgba(20, 23, 28, 0.65); }
  .empty-mark { display: grid; width: 42px; height: 42px; flex-shrink: 0; place-items: center; border-radius: 10px; background: rgba(59, 130, 246, 0.12); color: #60a5fa; font-size: 1.35rem; }
  .empty-state div { flex: 1; }
  .empty-state h2 { margin: 0 0 0.25rem; color: #e2e8f0; font-size: 1rem; }
  .empty-state p { margin: 0; color: #64748b; font-size: 0.8rem; }
  .enrolled-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
  .course-card { display: flex; min-height: 250px; flex-direction: column; padding: 1.4rem; border: 1px solid rgba(51, 65, 85, 0.68); border-radius: 13px; background: rgba(20, 23, 28, 0.82); color: inherit; transition: 150ms ease; }
  .course-card:hover { transform: translateY(-2px); border-color: rgba(96, 165, 250, 0.55); background: rgba(24, 28, 35, 0.95); }
  .course-card-link { display: flex; min-height: 0; flex: 1; flex-direction: column; color: inherit; text-decoration: none; }
  .card-topline, .card-footer, .catalog-meta { display: flex; align-items: center; gap: 0.65rem; color: #64748b; font-size: 0.72rem; }
  .card-topline { justify-content: space-between; }
  .course-card-link h2 { margin: 1rem 0 0.55rem; color: #f1f5f9; font-size: 1.05rem; }
  .course-card-link > p { display: -webkit-box; overflow: hidden; margin: 0; color: #94a3b8; font-size: 0.82rem; line-height: 1.65; line-clamp: 3; -webkit-box-orient: vertical; -webkit-line-clamp: 3; }
  .progress-track { height: 4px; margin-top: auto; overflow: hidden; border-radius: 999px; background: #202631; }
  .progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #2563eb, #60a5fa); }
  .card-footer { justify-content: space-between; padding-top: 0.9rem; }
  .card-footer-meta { display: flex; align-items: center; gap: 0.65rem; }
  .card-footer-meta form { display: flex; }
  .course-action { color: #bfdbfe; font-weight: 700; text-decoration: none; }
  .pause-button { padding: 0.25rem 0; border: 0; background: transparent; color: #64748b; font: inherit; cursor: pointer; }
  .pause-button:hover, .pause-button:focus-visible { color: #cbd5e1; text-decoration: underline; }
  .discover { margin-top: 4rem; padding-top: 2rem; border-top: 1px solid rgba(51, 65, 85, 0.48); scroll-margin-top: 1rem; }
  .discover-heading { margin-bottom: 1rem; }
  .discover-heading h2 { font-size: 1.55rem; }
  .discover-heading > span { color: #64748b; font-size: 0.75rem; }
  .catalog-list { overflow: hidden; border: 1px solid rgba(51, 65, 85, 0.58); border-radius: 13px; background: rgba(20, 23, 28, 0.55); }
  .catalog-row { display: flex; align-items: center; gap: 1.25rem; padding: 1.05rem 1.15rem; border-bottom: 1px solid rgba(51, 65, 85, 0.42); }
  .catalog-row:last-child { border-bottom: 0; }
  .catalog-copy { min-width: 0; flex: 1; color: inherit; text-decoration: none; }
  .catalog-title { display: flex; align-items: center; gap: 0.65rem; }
  .catalog-title h3 { margin: 0; color: #e2e8f0; font-size: 0.9rem; }
  .catalog-copy > p { overflow: hidden; margin: 0.3rem 0 0.55rem; color: #94a3b8; font-size: 0.76rem; text-overflow: ellipsis; white-space: nowrap; }
  .catalog-meta span + span::before { content: '/'; margin-right: 0.65rem; color: #334155; }
  .enroll-button { min-width: 78px; padding: 0.5rem 0.75rem; border: 1px solid rgba(96, 165, 250, 0.42); border-radius: 8px; background: rgba(37, 99, 235, 0.1); color: #bfdbfe; font-size: 0.76rem; font-weight: 750; cursor: pointer; }
  .enroll-button:hover { background: #2563eb; color: white; }
  .catalog-empty { color: #64748b; font-size: 0.85rem; }
  @media (max-width: 720px) {
    .tracks-main { padding: 2rem 1rem 4rem; }
    .library-header { align-items: flex-start; flex-direction: column; }
    .enrolled-grid { grid-template-columns: 1fr; }
    .empty-state { align-items: flex-start; flex-wrap: wrap; }
    .empty-state .btn-primary { width: 100%; }
    .catalog-row { align-items: stretch; flex-direction: column; }
    .catalog-row form, .enroll-button { width: 100%; }
  }
</style>
