<script lang="ts">
  /**
   * Header
   *
   * Top navigation bar. Shows the app name and a breadcrumb trail.
   */
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

  <div class="ml-auto flex items-center gap-3 text-xs text-slate-500">
    <span class="badge badge-blue">Local Mode</span>
    <!-- EXTENSION POINT: user avatar / auth button goes here in production -->
  </div>
</header>
