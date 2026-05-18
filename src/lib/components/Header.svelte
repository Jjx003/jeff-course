<script lang="ts">
  /**
   * Header
   *
   * Top navigation bar. Shows the app name, a breadcrumb trail, a streak
   * pill that links to /stats, and a small "Stats" tab.
   */
  import StreakBadge from './StreakBadge.svelte';
  import SessionPill from './SessionPill.svelte';

  interface Crumb {
    label: string;
    href?: string;
  }

  interface Props {
    crumbs?: Crumb[];
  }

  let { crumbs = [] }: Props = $props();
</script>

<header class="h-12 flex items-center px-4 border-b border-slate-700 bg-surface-900 flex-shrink-0 z-10">
  <!-- Logo / home link -->
  <a href="/" class="flex items-center gap-2 mr-4 no-underline">
    <span class="text-accent-400 font-bold text-base tracking-tight">ML&nbsp;Course</span>
  </a>

  <!-- Breadcrumbs -->
  {#if crumbs.length > 0}
    <nav aria-label="breadcrumb" class="flex items-center gap-1 text-sm min-w-0">
      {#each crumbs as crumb, i}
        {#if i > 0}
          <span class="text-slate-600">/</span>
        {/if}
        {#if crumb.href}
          <a href={crumb.href} class="text-slate-400 hover:text-slate-200 transition-colors truncate">
            {crumb.label}
          </a>
        {:else}
          <span class="text-slate-200 font-medium truncate">{crumb.label}</span>
        {/if}
      {/each}
    </nav>
  {/if}

  <div class="ml-auto flex items-center gap-3 text-xs">
    <SessionPill />
    <a href="/sessions" class="header-link" title="Running and recent sandbox sessions">Sessions</a>
    <a href="/stats" class="header-link" title="Your progress">Stats</a>
    <StreakBadge />
  </div>
</header>

<style>
  .header-link {
    color: #94a3b8;
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
    transition: color 0.15s, background 0.15s;
  }
  .header-link:hover {
    color: #e2e8f0;
    background: #1a1f2e;
  }
</style>
