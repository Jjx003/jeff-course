<script lang="ts">
  /**
   * TutorPanel — an AI tutor docked to the right edge of a module page.
   *
   * Works for every module type. The conversation is scoped to one module
   * and persisted per learner, so closing the drawer or reloading the page
   * keeps the thread. The module's own material is assembled server-side;
   * this component only sends the learner's message plus optional page
   * context (editor buffer, active tab).
   *
   * Collapsed by default so it never competes with the lesson for attention.
   */
  import { onMount, tick } from 'svelte';
  import { browser } from '$app/environment';
  import MarkdownRenderer from './MarkdownRenderer.svelte';
  import type { TutorConfig, TutorMessage } from '$lib/types/tutor.js';

  interface Props {
    trackSlug: string;
    problemSlug: string;
    problemTitle: string;
    /** Shown as a hint chip set; coding modules also get the code toggle. */
    isCoding?: boolean;
    /** Returns the current editor buffer, for coding modules. */
    getCode?: () => string | undefined;
    language?: string;
    activeTab?: string;
  }

  let {
    trackSlug,
    problemSlug,
    problemTitle,
    isCoding = false,
    getCode,
    language,
    activeTab
  }: Props = $props();

  const WIDTH_KEY = 'tutor-panel-width';
  const MIN_WIDTH = 300;
  const MAX_WIDTH = 720;

  let services: typeof import('$lib/services/index.js') | null = null;
  let open = $state(false);
  let config = $state<TutorConfig | null>(null);
  let messages = $state<TutorMessage[]>([]);
  let input = $state('');
  let streaming = $state(false);
  let errorMessage = $state<string | null>(null);
  let loadingThread = $state(false);
  let includeCode = $state(true);
  let width = $state(400);
  let resizing = $state(false);
  let scrollBox = $state<HTMLDivElement | undefined>(undefined);
  let textarea = $state<HTMLTextAreaElement | undefined>(undefined);
  let abortController: AbortController | null = null;
  /** Thread the panel currently holds, so module navigation can reset it. */
  let loadedThread = $state('');

  const SUGGESTIONS = [
    'Explain this in simpler terms',
    'Give me a hint, not the answer',
    'Why does this matter?',
    'Quiz me on this'
  ];
  const CODE_SUGGESTION = "What's wrong with my code?";

  let suggestions = $derived(isCoding ? [CODE_SUGGESTION, ...SUGGESTIONS] : SUGGESTIONS);
  let thread = $derived(`${trackSlug}/${problemSlug}`);

  onMount(async () => {
    const saved = localStorage.getItem(WIDTH_KEY);
    if (saved) width = clampWidth(parseInt(saved, 10));

    services = await import('$lib/services/index.js');
    try {
      config = await services.tutorService.getConfig();
    } catch {
      config = { enabled: false, model: '', reason: 'Could not reach the tutor service.' };
    }
  });

  function clampWidth(value: number): number {
    if (Number.isNaN(value)) return 400;
    return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, value));
  }

  // Navigating between modules must not carry the previous thread over.
  $effect(() => {
    const current = thread;
    if (current === loadedThread) return;
    loadedThread = current;
    stopStream();
    messages = [];
    errorMessage = null;
    if (open) void loadThread();
  });

  async function loadThread() {
    if (!services) return;
    loadingThread = true;
    try {
      messages = await services.tutorService.getConversation(trackSlug, problemSlug);
    } catch {
      messages = [];
    } finally {
      loadingThread = false;
      await scrollToBottom();
    }
  }

  async function toggleOpen() {
    open = !open;
    if (!open) return;
    if (!services) services = await import('$lib/services/index.js');
    if (messages.length === 0) await loadThread();
    await tick();
    textarea?.focus();
  }

  async function scrollToBottom() {
    await tick();
    scrollBox?.scrollTo({ top: scrollBox.scrollHeight });
  }

  function stopStream() {
    abortController?.abort();
    abortController = null;
    streaming = false;
  }

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || streaming || !services || !config?.enabled) return;

    input = '';
    errorMessage = null;
    const now = Date.now();
    messages = [
      ...messages,
      { id: `local-user-${now}`, role: 'user', content: question, createdAt: now },
      { id: `local-assistant-${now}`, role: 'assistant', content: '', createdAt: now }
    ];
    const replyIndex = messages.length - 1;
    streaming = true;
    await scrollToBottom();

    abortController = new AbortController();
    const code = isCoding && includeCode ? getCode?.() : undefined;

    await services.tutorService.ask(
      trackSlug,
      problemSlug,
      { message: question, code, language, activeTab },
      (chunk) => {
        if (chunk.kind === 'delta') {
          messages[replyIndex].content += chunk.text;
          void scrollToBottom();
        } else if (chunk.kind === 'done') {
          messages[replyIndex] = chunk.message;
        } else if (chunk.kind === 'error') {
          errorMessage = chunk.message;
          if (!messages[replyIndex].content) messages = messages.slice(0, replyIndex);
        }
      },
      { signal: abortController.signal }
    );

    abortController = null;
    streaming = false;
    await scrollToBottom();
  }

  async function clearThread() {
    if (!services || streaming) return;
    await services.tutorService.clearConversation(trackSlug, problemSlug);
    messages = [];
    errorMessage = null;
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  function onResizeStart(event: MouseEvent) {
    event.preventDefault();
    resizing = true;
  }

  $effect(() => {
    if (!browser || !resizing) return;
    const move = (e: MouseEvent) => {
      width = clampWidth(window.innerWidth - e.clientX);
    };
    const up = () => {
      resizing = false;
      localStorage.setItem(WIDTH_KEY, String(width));
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    return () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
  });

  // Ctrl/Cmd + I opens the tutor from anywhere on the page.
  function onWindowKeydown(event: KeyboardEvent) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'i') {
      event.preventDefault();
      void toggleOpen();
    } else if (event.key === 'Escape' && open && !streaming) {
      open = false;
    }
  }
</script>

<svelte:window onkeydown={onWindowKeydown} />

{#if !open}
  <button class="tutor-launcher" onclick={toggleOpen} title="Ask the AI tutor (Ctrl+I)">
    <span class="tutor-launcher-glyph">✦</span>
    Tutor
  </button>
{:else}
  <aside class="tutor-panel" style="width: {width}px" aria-label="AI tutor">
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="tutor-resizer"
      role="separator"
      aria-label="Resize tutor panel"
      aria-orientation="vertical"
      onmousedown={onResizeStart}
    ></div>

    <header class="tutor-header">
      <div class="tutor-title-group">
        <span class="tutor-title">AI Tutor</span>
        {#if config?.enabled}
          <span class="tutor-model" title="Model served through OpenRouter">{config.model}</span>
        {/if}
      </div>
      <div class="tutor-header-actions">
        <button
          class="tutor-icon-btn"
          onclick={clearThread}
          disabled={streaming || messages.length === 0}
          title="Clear this conversation"
        >Clear</button>
        <button class="tutor-icon-btn" onclick={toggleOpen} aria-label="Close tutor">×</button>
      </div>
    </header>

    <p class="tutor-scope">{problemTitle}</p>

    <div class="tutor-scroll" bind:this={scrollBox}>
      {#if config && !config.enabled}
        <div class="tutor-setup">
          <p class="tutor-setup-title">Tutor not configured</p>
          <p>{config.reason}</p>
          <pre class="tutor-setup-code">OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL={config.model}</pre>
          <p class="tutor-setup-note">
            Add these to your environment (or a <code>.env</code> file at the repo root) and
            restart the server. Keys stay on the machine running jeff-course.
          </p>
        </div>
      {:else if loadingThread}
        <p class="tutor-hint">Loading conversation…</p>
      {:else if messages.length === 0}
        <div class="tutor-empty">
          <p>
            Ask about anything on this page. The tutor already has this module's problem
            statement, theory, and tips — it will nudge you toward the answer rather than
            hand it over.
          </p>
        </div>
      {/if}

      {#each messages as message (message.id)}
        <div class="tutor-message" class:tutor-message-user={message.role === 'user'}>
          <span class="tutor-role">{message.role === 'user' ? 'You' : 'Tutor'}</span>
          {#if message.role === 'user'}
            <p class="tutor-user-text">{message.content}</p>
          {:else if message.content}
            <div class="tutor-markdown">
              <MarkdownRenderer content={message.content} variant="compact" headingPrefix="tutor" />
            </div>
          {:else}
            <span class="tutor-typing" aria-label="Tutor is thinking">●●●</span>
          {/if}
        </div>
      {/each}

      {#if errorMessage}
        <p class="tutor-error">{errorMessage}</p>
      {/if}
    </div>

    {#if config?.enabled}
      {#if messages.length === 0 && !loadingThread}
        <div class="tutor-suggestions">
          {#each suggestions as suggestion}
            <button class="tutor-chip" onclick={() => void send(suggestion)}>{suggestion}</button>
          {/each}
        </div>
      {/if}

      <div class="tutor-composer">
        {#if isCoding}
          <label class="tutor-code-toggle">
            <input type="checkbox" bind:checked={includeCode} />
            Share my current code
          </label>
        {/if}
        <textarea
          bind:this={textarea}
          bind:value={input}
          onkeydown={onKeydown}
          placeholder="Ask about this module…  (Enter to send)"
          rows="3"
        ></textarea>
        <div class="tutor-composer-actions">
          {#if streaming}
            <button class="tutor-send tutor-stop" onclick={stopStream}>Stop</button>
          {:else}
            <button class="tutor-send" onclick={() => void send()} disabled={!input.trim()}>
              Send
            </button>
          {/if}
        </div>
      </div>
    {/if}
  </aside>
{/if}

<style>
  .tutor-launcher {
    position: fixed;
    right: 0;
    bottom: 4.5rem;
    z-index: 60;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 0.8rem;
    border: 1px solid #334155;
    border-right: none;
    border-radius: 8px 0 0 8px;
    background: #131720;
    color: #cbd5e1;
    font-size: 0.78rem;
    font-weight: 600;
    box-shadow: -4px 0 18px rgb(0 0 0 / 0.35);
    cursor: pointer;
    transition: color 0.12s, background 0.12s, border-color 0.12s;
  }
  .tutor-launcher:hover {
    background: #1e293b;
    color: #f1f5f9;
    border-color: #475569;
  }
  .tutor-launcher-glyph {
    color: #60a5fa;
  }

  .tutor-panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 70;
    display: flex;
    flex-direction: column;
    min-width: 300px;
    max-width: 100vw;
    background: #0f1117;
    border-left: 1px solid #1e293b;
    box-shadow: -10px 0 40px rgb(0 0 0 / 0.45);
  }

  .tutor-resizer {
    position: absolute;
    top: 0;
    left: -3px;
    width: 6px;
    height: 100%;
    cursor: col-resize;
    background: transparent;
  }
  .tutor-resizer:hover {
    background: #2d3f5e;
  }

  .tutor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.6rem 0.75rem 0.5rem;
    border-bottom: 1px solid #1e293b;
    background: #131720;
    flex-shrink: 0;
  }
  .tutor-title-group {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    min-width: 0;
  }
  .tutor-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #e2e8f0;
  }
  .tutor-model {
    font-size: 0.65rem;
    color: #64748b;
    font-variant-numeric: tabular-nums;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .tutor-header-actions {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    flex-shrink: 0;
  }
  .tutor-icon-btn {
    padding: 0.15rem 0.45rem;
    border: 1px solid #334155;
    border-radius: 4px;
    background: transparent;
    color: #94a3b8;
    font-size: 0.7rem;
    line-height: 1.4;
    cursor: pointer;
    transition: color 0.1s, background 0.1s, border-color 0.1s;
  }
  .tutor-icon-btn:hover:not(:disabled) {
    background: #1e293b;
    color: #e2e8f0;
    border-color: #475569;
  }
  .tutor-icon-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .tutor-scope {
    padding: 0.4rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    color: #64748b;
    font-size: 0.7rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .tutor-scroll {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .tutor-empty,
  .tutor-hint,
  .tutor-setup {
    color: #94a3b8;
    font-size: 0.78rem;
    line-height: 1.6;
  }
  .tutor-setup {
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.75rem;
    background: #131720;
  }
  .tutor-setup-title {
    color: #fbbf24;
    font-weight: 600;
    margin-bottom: 0.35rem;
  }
  .tutor-setup-code {
    margin: 0.5rem 0;
    padding: 0.5rem 0.6rem;
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 4px;
    color: #cbd5e1;
    font-size: 0.7rem;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .tutor-setup-note code {
    color: #cbd5e1;
  }

  .tutor-message {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .tutor-role {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
  }
  .tutor-message-user .tutor-role {
    color: #60a5fa;
  }
  .tutor-user-text {
    white-space: pre-wrap;
    color: #e2e8f0;
    font-size: 0.82rem;
    line-height: 1.6;
    padding: 0.5rem 0.65rem;
    background: #1a2233;
    border: 1px solid #24344d;
    border-radius: 6px;
  }
  .tutor-markdown {
    font-size: 0.82rem;
    color: #cbd5e1;
  }
  .tutor-markdown :global(pre) {
    font-size: 0.72rem;
  }
  .tutor-typing {
    color: #475569;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    animation: tutor-pulse 1.2s ease-in-out infinite;
  }
  @keyframes tutor-pulse {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 1; }
  }

  .tutor-error {
    padding: 0.5rem 0.65rem;
    border: 1px solid #7f1d1d;
    border-radius: 6px;
    background: #2a0e0e;
    color: #fca5a5;
    font-size: 0.75rem;
    line-height: 1.5;
  }

  .tutor-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    padding: 0 0.75rem 0.5rem;
    flex-shrink: 0;
  }
  .tutor-chip {
    padding: 0.25rem 0.55rem;
    border: 1px solid #334155;
    border-radius: 999px;
    background: transparent;
    color: #94a3b8;
    font-size: 0.7rem;
    cursor: pointer;
    transition: color 0.1s, background 0.1s, border-color 0.1s;
  }
  .tutor-chip:hover {
    background: #1e293b;
    color: #e2e8f0;
    border-color: #475569;
  }

  .tutor-composer {
    flex-shrink: 0;
    padding: 0.6rem 0.75rem 0.75rem;
    border-top: 1px solid #1e293b;
    background: #131720;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }
  .tutor-code-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: #94a3b8;
    font-size: 0.7rem;
    cursor: pointer;
  }
  .tutor-composer textarea {
    width: 100%;
    resize: vertical;
    background: #0d1117;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    color: #e2e8f0;
    font-size: 0.8rem;
    line-height: 1.5;
    font-family: inherit;
  }
  .tutor-composer textarea:focus {
    outline: none;
    border-color: #60a5fa;
  }
  .tutor-composer-actions {
    display: flex;
    justify-content: flex-end;
  }
  .tutor-send {
    padding: 0.3rem 0.9rem;
    border: 1px solid #2563eb;
    border-radius: 6px;
    background: #1d4ed8;
    color: #f8fafc;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.1s, opacity 0.1s;
  }
  .tutor-send:hover:not(:disabled) {
    background: #2563eb;
  }
  .tutor-send:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .tutor-stop {
    background: #7f1d1d;
    border-color: #991b1b;
  }
  .tutor-stop:hover {
    background: #991b1b;
  }
</style>
