<script lang="ts">
  /**
   * ReadingView — textbook-style full-width layout for `type: reading` modules.
   *
   * Unlike the coding view, there is no editor, no runner, and no tab group.
   * The full markdown body (problem.md + optional theory.md) is rendered in
   * a single scrolling column. Designed for chemistry/biology background
   * content where code execution doesn't apply.
   */
  import Header from '$lib/components/Header.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import ProblemNav from '$lib/components/ProblemNav.svelte';
  import type { Problem, ProblemMeta, Track } from '$lib/types/course.js';

  interface Props {
    track: Track;
    problem: Problem;
    prevProblem: ProblemMeta | null;
    nextProblem: ProblemMeta | null;
  }

  let { track, problem, prevProblem, nextProblem }: Props = $props();

  const DIFFICULTY_BADGE: Record<string, string> = {
    beginner:     'badge-green',
    intermediate: 'badge-yellow',
    advanced:     'badge-red'
  };

  let hasTheory = $derived(problem.tabs.theory.trim().length > 0);
  let hasFurther = $derived(problem.tabs.tips.trim().length > 0);
</script>

<div class="reading-shell">
  <Header
    crumbs={[
      { label: 'Tracks', href: '/tracks' },
      { label: track.title, href: `/tracks/${track.slug}` },
      { label: problem.title }
    ]}
  />

  <main class="reading-main">
    <article class="reading-article">
      <!-- Meta header -->
      <header class="reading-header">
        <div class="reading-eyebrow">
          <span class="text-slate-500 font-mono text-xs">
            {track.title} · Module {problem.order.toString().padStart(2, '0')}
          </span>
        </div>
        <h1 class="reading-title">{problem.title}</h1>
        <div class="reading-meta">
          <span class="badge {DIFFICULTY_BADGE[problem.difficulty] ?? 'badge-blue'}">
            {problem.difficulty}
          </span>
          <span class="text-xs text-slate-500">{problem.estimatedMinutes} min read</span>
          {#each problem.tags as tag}
            <span class="badge badge-blue">{tag}</span>
          {/each}
        </div>
        {#if problem.description}
          <p class="reading-description">{problem.description}</p>
        {/if}
      </header>

      <!-- Main body (problem.md) -->
      <section class="reading-body">
        <MarkdownRenderer content={problem.tabs.problem} />
      </section>

      <!-- Optional theory.md as a deep-dive appendix -->
      {#if hasTheory}
        <section class="reading-section">
          <h2 class="reading-section-title">Deep dive</h2>
          <MarkdownRenderer content={problem.tabs.theory} />
        </section>
      {/if}

      <!-- Optional tips.md repurposed as "further reading" -->
      {#if hasFurther}
        <section class="reading-section">
          <h2 class="reading-section-title">Further reading</h2>
          <MarkdownRenderer content={problem.tabs.tips} />
        </section>
      {/if}

      <!-- Footer navigation -->
      <footer class="reading-footer">
        <ProblemNav
          trackSlug={track.slug}
          {prevProblem}
          {nextProblem}
        />
      </footer>
    </article>
  </main>
</div>

<style>
  .reading-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    background: #0f1117;
  }

  .reading-main {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 1.5rem 4rem;
  }

  .reading-article {
    max-width: 760px;
    margin: 0 auto;
  }

  .reading-header {
    padding-bottom: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid #1e293b;
  }

  .reading-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
  }

  .reading-title {
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 1rem;
  }

  .reading-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.25rem;
  }

  .reading-description {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.6;
    margin: 0;
  }

  .reading-body :global(.prose),
  .reading-section :global(.prose) {
    /* Tighter padding than the split-pane prose, which is intentionally cramped */
    padding-left: 0;
    padding-right: 0;
  }

  .reading-section {
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid #1e293b;
  }

  .reading-section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0 0 0.5rem;
    letter-spacing: -0.01em;
  }

  .reading-footer {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #1e293b;
  }
</style>
