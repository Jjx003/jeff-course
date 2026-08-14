<script lang="ts">
  /**
   * Header
   *
   * Top navigation bar. Shows the app name, a breadcrumb trail, a streak
   * pill that links to /stats, and a small "Stats" tab.
   */
  import { APP_NAME } from '$lib/config/app.js';
  import { page } from '$app/state';
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

<header class="site-header">
  <a href="/" class="brand" aria-label="{APP_NAME} home">
    <span class="brand-mark" aria-hidden="true">J</span>
    <span class="brand-name">{APP_NAME}</span>
  </a>

  <!-- Breadcrumbs -->
  {#if crumbs.length > 0}
    <nav aria-label="breadcrumb" class="breadcrumbs">
      {#each crumbs as crumb, i}
        {#if i > 0}
          <span class="crumb-separator" aria-hidden="true">/</span>
        {/if}
        {#if crumb.href}
          <a href={crumb.href} class="crumb-link">
            {crumb.label}
          </a>
        {:else}
          <span class="crumb-current">{crumb.label}</span>
        {/if}
      {/each}
    </nav>
  {/if}

  <nav class="header-actions" aria-label="Primary navigation">
    <SessionPill />
    <a href="/sessions" class="header-link" class:active={page.url.pathname.startsWith('/sessions')} title="Running and recent sandbox sessions">Sessions</a>
    <a href="/stats" class="header-link" class:active={page.url.pathname.startsWith('/stats')} title="Your progress">Stats</a>
    {#if page.data.user}
      <a href="/auth/sign-in" class="profile-link" title="Switch profile">
        <span class="profile-dot" aria-hidden="true"></span>
        <span>{page.data.user.name}</span>
      </a>
    {/if}
    <StreakBadge />
  </nav>
</header>

<style>
  .site-header {
    z-index: 30;
    display: flex;
    flex-shrink: 0;
    align-items: center;
    min-height: 56px;
    padding: 0 1.1rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.6);
    background: rgba(18, 21, 26, 0.9);
    backdrop-filter: blur(16px);
  }
  .brand { display: inline-flex; align-items: center; gap: 0.65rem; margin-right: 1.1rem; color: #f8fafc; text-decoration: none; }
  .brand-mark { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border: 1px solid rgba(96, 165, 250, 0.45); border-radius: 8px; background: linear-gradient(145deg, rgba(59, 130, 246, 0.24), rgba(30, 41, 59, 0.5)); color: #93c5fd; font-size: 0.82rem; font-weight: 800; box-shadow: inset 0 1px rgba(255, 255, 255, 0.05); }
  .brand-name { font-size: 0.9rem; font-weight: 750; letter-spacing: -0.02em; }
  .breadcrumbs { display: flex; min-width: 0; align-items: center; gap: 0.45rem; font-size: 0.78rem; }
  .crumb-separator { color: #475569; }
  .crumb-link, .crumb-current { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .crumb-link { color: #94a3b8; text-decoration: none; transition: color 150ms ease; }
  .crumb-link:hover { color: #e2e8f0; }
  .crumb-current { color: #cbd5e1; font-weight: 600; }
  .header-actions { display: flex; align-items: center; gap: 0.25rem; margin-left: auto; font-size: 0.75rem; }
  .header-link {
    color: #94a3b8;
    text-decoration: none;
    padding: 0.4rem 0.65rem;
    border-radius: 7px;
    font-weight: 600;
    transition: color 0.15s, background 0.15s;
  }
  .header-link:hover, .header-link.active {
    color: #e2e8f0;
    background: rgba(51, 65, 85, 0.42);
  }
  .profile-link { display: inline-flex; align-items: center; gap: 0.45rem; max-width: 10rem; padding: 0.4rem 0.6rem; border: 1px solid rgba(51, 65, 85, 0.65); border-radius: 999px; color: #cbd5e1; text-decoration: none; }
  .profile-link span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .profile-dot { width: 6px; height: 6px; flex-shrink: 0; border-radius: 999px; background: #60a5fa; box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.12); }
  @media (max-width: 720px) {
    .site-header { min-height: 52px; padding: 0 0.75rem; }
    .brand { margin-right: 0.75rem; }
    .brand-name, .breadcrumbs, .header-link:first-of-type { display: none; }
    .header-actions { gap: 0.1rem; }
    .profile-link { max-width: 7rem; border-color: transparent; }
  }
</style>
