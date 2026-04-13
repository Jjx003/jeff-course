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
   * - Exposes `getValue()` for Run/Submit to read current code
   * - Exposes `setValue(code)` for language switching
   *
   * Monaco is loaded dynamically inside onMount (browser-only).
   * A no-op worker blob is provided so Monaco doesn't error on missing workers.
   * This is sufficient for syntax highlighting of Python/C++ via Monarch tokenizers.
   */

  import { onMount, onDestroy } from 'svelte';
  import type { Language } from '$lib/types/course.js';

  interface Props {
    language: Language;
    initialValue: string;
    fontSize?: number;
    onsave?: (code: string) => void;
    onready?: () => void;
  }

  let { language, initialValue, fontSize = 14, onsave, onready }: Props = $props();

  let container: HTMLDivElement;
  let editor: import('monaco-editor').editor.IStandaloneCodeEditor | null = null;
  let monacoLib: typeof import('monaco-editor') | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let mounted = $state(false);

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
      editor?.dispose();
    };
  });

  onDestroy(() => {
    saveTimer && clearTimeout(saveTimer);
    editor?.dispose();
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
</div>

<style>
  .editor-wrap {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .editor-container {
    width: 100%;
    height: 100%;
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
