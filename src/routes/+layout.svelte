<script lang="ts">
  import '../app.css';
  import { APP_DESCRIPTION, APP_NAME } from '$lib/config/app.js';

  interface Props {
    children: import('svelte').Snippet;
  }

  let { children }: Props = $props();
</script>

<svelte:head>
  <title>{APP_NAME}</title>
  <meta name="description" content={APP_DESCRIPTION} />
</svelte:head>

<div class="app-shell">
  {@render children()}
</div>

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
    overscroll-behavior: none;
  }
</style>
