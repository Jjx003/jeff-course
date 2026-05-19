<script lang="ts">
  import '../app.css';

  interface Props {
    children: import('svelte').Snippet;
  }

  let { children }: Props = $props();
</script>

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
