import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],

  // Monaco Editor is browser-only; exclude from SSR bundle analysis.
  // Workers are handled with no-op blobs inside CodeEditor.svelte (onMount only).
  // duckdb uses native binaries — must remain external so Vite doesn't try to bundle it.
  ssr: {
    noExternal: [],
    external: ['duckdb']
  },

  optimizeDeps: {
    // Pre-bundle monaco-editor so Vite doesn't re-process it on every page load.
    include: ['monaco-editor']
  },

  // Allow the dev server to serve files from the courses directory.
  server: {
    fs: {
      allow: ['..']
    }
  }
});
