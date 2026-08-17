<script lang="ts">
  /**
   * CodeEditor
   *
   * Monaco-based code editor component.
   *
   * Features:
   * - Python and C++ syntax highlighting
   * - Dark theme (course-dark)
   * - Auto-saves draft on every change (debounced 800ms)
   * - Optional vim keybindings (monaco-vim) with a status line
   * - Exposes `getValue()` for Run/Submit to read current code
   * - Exposes `setValue(code)` for language switching
   *
   * Monaco is loaded dynamically inside onMount (browser-only).
   * A no-op worker blob is provided so Monaco doesn't error on missing workers.
   * This is sufficient for syntax highlighting of Python/C++ via Monarch tokenizers.
   *
   * monaco-vim is also loaded dynamically, but only the first time vim mode is
   * turned on — users who never enable it never pay for the chunk.
   */

  import { onMount, onDestroy } from 'svelte';
  import type { Language } from '$lib/types/course.js';

  interface Props {
    language: Language;
    initialValue: string;
    fontSize?: number;
    /** Enable vim keybindings. */
    vim?: boolean;
    onsave?: (code: string) => void;
    onready?: () => void;
  }

  let { language, initialValue, fontSize = 14, vim = false, onsave, onready }: Props = $props();

  let container: HTMLDivElement;
  let vimStatusBar: HTMLDivElement;
  let editor: import('monaco-editor').editor.IStandaloneCodeEditor | null = null;
  let monacoLib: typeof import('monaco-editor') | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let mounted = $state(false);

  /** Live monaco-vim binding; null whenever vim mode is off. */
  let vimBinding: { dispose(): void } | null = null;
  /** Guards against overlapping enable/disable while the chunk is loading. */
  let vimPending = false;

  const MONACO_LANG: Record<Language, string> = {
    python: 'python',
    cpp: 'cpp'
  };

  onMount(() => {
    // Run async init without making onMount itself async (which breaks cleanup return).
    (async () => {
      // No-op MonacoEnvironment — prevents worker-not-found errors.
      // EXTENSION POINT: swap for real worker URLs in a production build.
      (window as unknown as Record<string, unknown>).MonacoEnvironment = {
        getWorker: (_moduleId: string, _label: string): Worker => {
          const blob = new Blob(['self.onmessage=function(){}'], {
            type: 'application/javascript'
          });
          return new Worker(URL.createObjectURL(blob));
        }
      };

      monacoLib = await import('monaco-editor');

      monacoLib.editor.defineTheme('course-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token: 'comment',  foreground: '6A9955', fontStyle: 'italic' },
          { token: 'keyword',  foreground: 'C586C0' },
          { token: 'string',   foreground: 'CE9178' },
          { token: 'number',   foreground: 'B5CEA8' },
          { token: 'type',     foreground: '4EC9B0' },
          { token: 'function', foreground: 'DCDCAA' }
        ],
        colors: {
          'editor.background':               '#0f1117',
          'editor.lineHighlightBackground':  '#1a1f2e',
          'editorLineNumber.foreground':     '#4a5568',
          'editorLineNumber.activeForeground':'#a0aec0',
          'editor.selectionBackground':      '#264f78',
          'editorIndentGuide.background1':   '#2d3748'
        }
      });

      editor = monacoLib.editor.create(container, {
        value: initialValue,
        language: MONACO_LANG[language],
        theme: 'course-dark',
        fontSize,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        fontLigatures: true,
        lineHeight: 22,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        tabSize: 4,
        insertSpaces: true,
        automaticLayout: true,
        padding: { top: 12, bottom: 12 },
        renderWhitespace: 'boundary',
        bracketPairColorization: { enabled: true },
        suggest: { showWords: true },
        quickSuggestions: { other: true, comments: false, strings: false },
        parameterHints: { enabled: true },
        scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 }
      });

      editor.onDidChangeModelContent(() => {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
          const code = editor?.getValue() ?? '';
          onsave?.(code);
        }, 800);
      });

      mounted = true;
      onready?.();
    })();

    // Return synchronous cleanup
    return () => {
      saveTimer && clearTimeout(saveTimer);
      vimBinding?.dispose();
      vimBinding = null;
      editor?.dispose();
    };
  });

  onDestroy(() => {
    saveTimer && clearTimeout(saveTimer);
    vimBinding?.dispose();
    vimBinding = null;
    editor?.dispose();
  });

  /** Write the current buffer through the normal draft-save path, right now. */
  function flushSave() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = null;
    onsave?.(editor?.getValue() ?? '');
  }

  async function enableVim() {
    if (!editor || vimBinding || vimPending) return;
    vimPending = true;
    try {
      const { initVimMode, VimMode } = await import('monaco-vim');

      // `:w` flushes the draft instead of erroring out — drafts already
      // autosave, so this just makes the muscle memory harmless.
      // `Vim` is present at runtime but missing from monaco-vim's type surface.
      const vimApi = (VimMode as unknown as { Vim: { defineEx: (n: string, p: string, f: () => void) => void } }).Vim;
      vimApi.defineEx('write', 'w', flushSave);

      // The editor may have been torn down while the chunk was loading.
      if (!editor) return;
      vimBinding = initVimMode(editor, vimStatusBar);
    } finally {
      vimPending = false;
    }
  }

  function disableVim() {
    vimBinding?.dispose();
    vimBinding = null;
    if (vimStatusBar) {
      vimStatusBar.textContent = '';
      // monaco-vim writes an inline `display` on the status node, which would
      // otherwise beat the .vim-status-hidden class and leave an empty bar.
      vimStatusBar.style.removeProperty('display');
    }
    editor?.focus();
  }

  // Toggle vim mode when the prop changes (and once the editor exists).
  $effect(() => {
    const wantVim = vim;
    if (!mounted) return;
    if (wantVim) enableVim();
    else disableVim();
  });

  // Sync language when prop changes
  $effect(() => {
    if (!editor || !monacoLib) return;
    const model = editor.getModel();
    if (model) {
      monacoLib.editor.setModelLanguage(model, MONACO_LANG[language]);
    }
  });

  // Sync font size when prop changes (gate on mounted so editor exists)
  $effect(() => {
    if (!mounted) return;
    editor?.updateOptions({ fontSize });
  });

  export function getValue(): string {
    return editor?.getValue() ?? '';
  }

  export function setValue(code: string) {
    if (!editor) return;
    editor.setValue(code);
    editor.setPosition({ lineNumber: 1, column: 1 });
    editor.revealPosition({ lineNumber: 1, column: 1 });
  }
</script>

<div class="editor-wrap">
  {#if !mounted}
    <div class="editor-placeholder">
      <span class="loader"></span>
      Loading editor…
    </div>
  {/if}
  <div bind:this={container} class="editor-container" class:invisible={!mounted}></div>
  <!-- Vim status line: kept mounted but collapsed so the node exists before initVimMode runs. -->
  <div bind:this={vimStatusBar} class="vim-status" class:vim-status-hidden={!vim}></div>
</div>

<style>
  .editor-wrap {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
  }

  .editor-container {
    width: 100%;
    flex: 1;
    min-height: 0;
  }

  /* Vim status line — mirrors the editor chrome, sits under the buffer.
     Block (not flex) on purpose: monaco-vim writes `display: block` inline on
     this node, so an inline layout is the one that actually survives. */
  .vim-status {
    flex: 0 0 auto;
    height: 1.5rem;
    padding: 0 0.5rem;
    background: #161a24;
    border-top: 1px solid #1f2937;
    color: #94a3b8;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.72rem;
    line-height: 1.5rem;
    white-space: nowrap;
    overflow: hidden;
  }

  .vim-status-hidden {
    display: none;
  }

  /* monaco-vim builds these nodes itself, so they need :global to be styled. */
  .vim-status :global(span) {
    color: inherit;
    margin-right: 0.75rem;
  }

  /* The `:` / `/` command line. */
  .vim-status :global(input) {
    width: 60%;
    background: transparent;
    border: none;
    outline: none;
    color: #e2e8f0;
    font: inherit;
    line-height: inherit;
  }

  .editor-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: #64748b;
    font-size: 0.875rem;
    background: #0f1117;
  }

  .loader {
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    border: 2px solid #334155;
    border-top-color: #60a5fa;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .invisible { visibility: hidden; }
</style>
