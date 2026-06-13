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

<div class="problem-nav">
  {#if prevProblem}
    <a href={href(prevProblem.slug)} class="nav-link group">
      <span class="nav-arrow" aria-hidden="true">&larr;</span>
      <div class="nav-copy nav-copy-prev">
        <div class="nav-label">Previous</div>
        <div class="nav-title">{prevProblem.title}</div>
      </div>
    </a>
  {:else}
    <div></div>
  {/if}

  {#if nextProblem}
    <a href={href(nextProblem.slug)} class="nav-link group text-right">
      <div class="nav-copy nav-copy-next">
        <div class="nav-label">Next</div>
        <div class="nav-title">{nextProblem.title}</div>
      </div>
      <span class="nav-arrow" aria-hidden="true">&rarr;</span>
    </a>
  {:else}
    <div></div>
  {/if}
</div>

<style>
  .problem-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.75rem 1.5rem;
    border-top: 1px solid #334155;
    flex-shrink: 0;
  }

  .nav-link {
    display: flex;
    align-items: center;
    min-width: 0;
    max-width: min(48%, 24rem);
    padding: 0.375rem 0.5rem;
    border-radius: 0.375rem;
    color: inherit;
    text-decoration: none;
    transition: background 150ms;
  }

  .nav-link:hover {
    background: rgb(30 41 59 / 0.6);
  }

  .nav-arrow {
    color: #64748b;
    transition: color 150ms;
  }

  .nav-link:hover .nav-arrow {
    color: #cbd5e1;
  }

  .nav-copy {
    min-width: 0;
  }

  .nav-copy-prev {
    margin-left: 0.5rem;
  }

  .nav-copy-next {
    margin-right: 0.5rem;
  }

  .nav-label {
    color: #64748b;
    font-size: 0.75rem;
    transition: color 150ms;
  }

  .nav-title {
    overflow: hidden;
    color: #cbd5e1;
    font-size: 0.875rem;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: color 150ms;
  }

  .nav-link:hover .nav-label {
    color: #94a3b8;
  }

  .nav-link:hover .nav-title {
    color: #fff;
  }

  @media (max-width: 520px) {
    .problem-nav {
      padding: 0.75rem;
    }

    .nav-link {
      max-width: 50%;
      padding: 0.35rem;
    }

    .nav-title {
      max-width: 8.5rem;
      font-size: 0.8rem;
    }
  }
</style>
