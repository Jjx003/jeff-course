<script lang="ts">
  /**
   * LanguageSwitcher
   *
   * Renders toggle buttons for switching between supported languages.
   * Switching language triggers `onchange`; the parent is responsible for
   * loading the correct draft and updating the editor content.
   */
  import type { Language } from '$lib/types/course.js';

  interface Props {
    languages: Language[];
    current: Language;
    onchange: (lang: Language) => void;
  }

  let { languages, current, onchange }: Props = $props();

  const LABELS: Record<Language, string> = {
    python: 'Python',
    cpp: 'C++'
  };
</script>

<div class="flex items-center gap-1 rounded-md bg-surface-900 p-0.5 border border-slate-700">
  {#each languages as lang}
    <button
      class="px-3 py-1 rounded text-xs font-medium transition-colors duration-150"
      class:active={lang === current}
      onclick={() => onchange(lang)}
      title="Switch to {LABELS[lang]}"
    >
      {LABELS[lang]}
    </button>
  {/each}
</div>

<style>
  button {
    color: #94a3b8; /* slate-400 */
    background: transparent;
  }
  button:hover {
    color: #e2e8f0; /* slate-200 */
    background: #1e293b; /* slate-800 */
  }
  button.active {
    color: #60a5fa; /* accent-400 */
    background: #1e3a5f; /* custom dark blue */
  }
</style>
