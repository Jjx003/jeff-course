<script lang="ts">
  /**
   * ProblemNav
   *
   * Previous / Next navigation links for moving between problems in a track.
   */
  import type { ProblemMeta } from '$lib/types/course.js';

  interface Props {
    trackSlug: string;
    prevProblem?: ProblemMeta | null;
    nextProblem?: ProblemMeta | null;
  }

  let { trackSlug, prevProblem = null, nextProblem = null }: Props = $props();

  function href(slug: string) {
    return `/tracks/${trackSlug}/problems/${slug}`;
  }
</script>

<div class="flex items-center justify-between px-6 py-3 border-t border-slate-700 flex-shrink-0">
  {#if prevProblem}
    <a href={href(prevProblem.slug)} class="nav-link group">
      <span class="text-slate-500 group-hover:text-slate-300 transition-colors">←</span>
      <div class="ml-2">
        <div class="text-xs text-slate-500 group-hover:text-slate-400">Previous</div>
        <div class="text-sm text-slate-300 group-hover:text-white truncate max-w-[140px]">
          {prevProblem.title}
        </div>
      </div>
    </a>
  {:else}
    <div></div>
  {/if}

  {#if nextProblem}
    <a href={href(nextProblem.slug)} class="nav-link group text-right">
      <div class="mr-2">
        <div class="text-xs text-slate-500 group-hover:text-slate-400">Next</div>
        <div class="text-sm text-slate-300 group-hover:text-white truncate max-w-[140px]">
          {nextProblem.title}
        </div>
      </div>
      <span class="text-slate-500 group-hover:text-slate-300 transition-colors">→</span>
    </a>
  {:else}
    <div></div>
  {/if}
</div>

<style>
  .nav-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    padding: 0.375rem 0.5rem;
    border-radius: 0.375rem;
    transition: background 150ms;
  }
  .nav-link:hover {
    background: rgb(30 41 59 / 0.6); /* slate-800/60 */
  }
</style>
