<script lang="ts">
  import Header from '$lib/components/Header.svelte';
</script>

<Header />

<main class="flex-1 overflow-y-auto flex flex-col items-center justify-center px-6 py-16 text-center">
  <h1 class="text-4xl font-bold text-slate-100 mb-4 tracking-tight">
    ML Coding Course
  </h1>
  <p class="text-lg text-slate-400 max-w-xl mb-10">
    Interactive machine-learning exercises with a real code editor, local persistence,
    and filesystem-driven course content.
  </p>

  <a href="/tracks" class="btn-primary text-base px-6 py-2.5">
    Browse Tracks →
  </a>

  <div class="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-2xl w-full text-left">
    {#each features as f}
      <div class="rounded-xl border border-slate-700 bg-surface-900 p-5">
        <div class="text-2xl mb-3">{f.icon}</div>
        <h3 class="text-sm font-semibold text-slate-200 mb-1">{f.title}</h3>
        <p class="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
      </div>
    {/each}
  </div>
</main>

<script lang="ts" context="module">
  const features = [
    {
      icon: '📝',
      title: 'Filesystem-driven content',
      desc: 'Add a new problem by dropping Markdown files into a folder — no app code to edit.'
    },
    {
      icon: '💾',
      title: 'Local persistence',
      desc: 'Your code drafts, run history, and submissions are saved locally in your browser.'
    },
    {
      icon: '⚡',
      title: 'Monaco editor',
      desc: 'Full IDE-quality editor with Python and C++ syntax highlighting.'
    }
  ];
</script>
