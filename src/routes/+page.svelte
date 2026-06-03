<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import { APP_DESCRIPTION, APP_NAME, APP_TAGLINE } from '$lib/config/app.js';

  const features = [
    {
      icon: '📝',
      kicker: '01',
      title: 'Courses as files',
      desc: 'Create or share a track by copying YAML, Markdown, quizzes, drills, and starter code into a folder.'
    },
    {
      icon: '💾',
      kicker: '02',
      title: 'Local progress',
      desc: 'Drafts, submissions, completions, study time, and achievements are stored in a local DuckDB file.'
    },
    {
      icon: '⚡',
      kicker: '03',
      title: 'Practice modes',
      desc: 'Mix readings, coding exercises, quizzes, tests, and timed drills in the same course.'
    },
    {
      icon: '🔥',
      kicker: '04',
      title: 'Calm momentum',
      desc: 'A streak, points, and a year-long activity heatmap to keep you showing up.'
    }
  ];
</script>

<Header />

<main class="flex-1 overflow-y-auto flex flex-col items-center justify-center px-6 py-16 text-center">
  <p class="mb-3 inline-flex items-center gap-2 text-sm font-semibold text-accent-300 tracking-wide">
    <span aria-hidden="true">✨</span>
    <span>{APP_TAGLINE}</span>
  </p>
  <h1 class="text-4xl font-bold text-slate-100 mb-4 tracking-tight">
    {APP_NAME}
  </h1>
  <p class="text-lg text-slate-400 max-w-xl mb-10">
    {APP_DESCRIPTION}
  </p>

  <div class="flex items-center gap-3">
    <a href="/tracks" class="btn-primary text-base px-6 py-2.5">
      Browse Tracks <span aria-hidden="true">→</span>
    </a>
    <a href="/stats" class="btn-ghost text-base px-5 py-2.5">
      View Progress
    </a>
  </div>

  <div class="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl w-full text-left">
    {#each features as f}
      <div class="rounded-lg border border-slate-700 bg-surface-900 p-5 transition hover:-translate-y-0.5 hover:border-accent-700 hover:bg-surface-800">
        <div class="mb-4 flex items-center justify-between">
          <span class="text-2xl" aria-hidden="true">{f.icon}</span>
          <span class="text-xs font-semibold text-accent-300">{f.kicker}</span>
        </div>
        <h3 class="text-sm font-semibold text-slate-200 mb-1">{f.title}</h3>
        <p class="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
      </div>
    {/each}
  </div>
</main>
