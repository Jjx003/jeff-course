<script lang="ts">
  /**
   * TutorPanel — an AI tutor docked to the right edge of a module page.
   *
   * Works for every module type. The conversation is scoped to one module
   * and persisted per learner, so closing the drawer or reloading the page
   * keeps the thread.
   *
   * The panel sends only the learner's message plus which language/tab they
   * have open. The tutor reads the module material, the editor buffer, run
   * output, and grader verdicts server-side through tools, and the tool
   * activity is streamed back so the learner can see what it looked at.
   *
   * Collapsed by default so it never competes with the lesson for attention.
   */
  import { onMount, tick } from 'svelte';
  import { browser } from '$app/environment';
  import MarkdownRenderer from './MarkdownRenderer.svelte';
  import type { TutorConfig, TutorMessage, TutorToolStep } from '$lib/types/tutor.js';

  interface Props {
    trackSlug: string;
    problemSlug: string;
    problemTitle: string;
    /** Coding modules get code-aware suggestions and a richer scope note. */
    isCoding?: boolean;
    /**
     * Flush any pending editor autosave before the tutor reads the draft.
     * Without this a question asked mid-keystroke sees stale code.
     */
    flushDraft?: () => Promise<void> | void;
    language?: string;
    activeTab?: string;
  }

  let {
    trackSlug,
    problemSlug,
    problemTitle,
    isCoding = false,
    flushDraft,
    language,
    activeTab
  }: Props = $props();

  const WIDTH_KEY = 'tutor-panel-width';
  const MIN_WIDTH = 320;
  const MAX_WIDTH = 760;
  /** How far off the bottom counts as "the learner scrolled up to read". */
  const STICK_THRESHOLD = 80;

  let services: typeof import('$lib/services/index.js') | null = null;
  let open = $state(false);
  let config = $state<TutorConfig | null>(null);
  let messages = $state<TutorMessage[]>([]);
  let input = $state('');
  let streaming = $state(false);
  let errorMessage = $state<string | null>(null);
  let loadingThread = $state(false);
  let width = $state(420);
  let resizing = $state(false);
  let scrollBox = $state<HTMLDivElement | undefined>(undefined);
  let textarea = $state<HTMLTextAreaElement | undefined>(undefined);
  let abortController: AbortController | null = null;
  /** Thread the panel currently holds, so module navigation can reset it. */
  let loadedThread = $state('');
  /**
   * A step as the panel renders it. `pending` is view-only state: the
   * persisted shape has no notion of "still running".
   */
  type RenderStep = TutorToolStep & { pending: boolean };

  /** Tool steps for the reply being streamed right now. */
  let liveSteps = $state<RenderStep[]>([]);
  /** Set while a tool is running but the model has produced no prose yet. */
  let activeToolLabel = $state<string | null>(null);
  /** Last question asked, so a failed turn can be retried. */
  let lastQuestion = $state('');
  let copiedId = $state<string | null>(null);
  /** False once the learner scrolls up, so streaming doesn't yank them back. */
  let stickToBottom = $state(true);

  const SUGGESTIONS = [
    'Explain this in simpler terms',
    'Give me a hint, not the answer',
    'Why does this matter?',
    'Quiz me on this'
  ];
  const CODING_SUGGESTIONS = ["What's wrong with my code?", 'Why did my last run fail?'];

  let suggestions = $derived(isCoding ? [...CODING_SUGGESTIONS, ...SUGGESTIONS] : SUGGESTIONS);
  let thread = $derived(`${trackSlug}/${problemSlug}`);
  let canSend = $derived(Boolean(input.trim()) && !streaming && Boolean(config?.enabled));

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
    if (Number.isNaN(value)) return 420;
    return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, value));
  }

  // Navigating between modules must not carry the previous thread over.
  $effect(() => {
    const current = thread;
    if (current === loadedThread) return;
    loadedThread = current;
    stopStream();
    messages = [];
    liveSteps = [];
    activeToolLabel = null;
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
      stickToBottom = true;
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

  /** Coalesces the many scroll requests a stream produces into one per frame. */
  let scrollQueued = false;
  function scrollSoon() {
    if (scrollQueued || !browser) return;
    scrollQueued = true;
    requestAnimationFrame(() => {
      scrollQueued = false;
      if (scrollBox) scrollBox.scrollTop = scrollBox.scrollHeight;
    });
  }

  function onScroll() {
    if (!scrollBox) return;
    const distance = scrollBox.scrollHeight - scrollBox.scrollTop - scrollBox.clientHeight;
    stickToBottom = distance <= STICK_THRESHOLD;
  }

  /** Only follow the stream while the learner is already at the bottom. */
  function followStream() {
    if (stickToBottom) scrollSoon();
  }

  function stopStream() {
    abortController?.abort();
    abortController = null;
    streaming = false;
    activeToolLabel = null;
  }

  function autoGrow() {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || streaming || !services || !config?.enabled) return;

    // The editor autosaves on a debounce; make sure the tutor's tools see
    // what is on screen rather than what was there a second ago.
    if (isCoding && flushDraft) {
      try {
        await flushDraft();
      } catch {
        /* a failed flush just means slightly stale code */
      }
    }

    input = '';
    await tick();
    autoGrow();
    errorMessage = null;
    lastQuestion = question;
    liveSteps = [];
    activeToolLabel = null;

    const now = Date.now();
    messages = [
      ...messages,
      { id: `local-user-${now}`, role: 'user', content: question, createdAt: now },
      { id: `local-assistant-${now}`, role: 'assistant', content: '', createdAt: now }
    ];
    const replyIndex = messages.length - 1;
    streaming = true;
    stickToBottom = true;
    await scrollToBottom();

    abortController = new AbortController();

    await services.tutorService.ask(
      trackSlug,
      problemSlug,
      { message: question, language, activeTab },
      (chunk) => {
        if (chunk.kind === 'delta') {
          messages[replyIndex].content += chunk.text;
          activeToolLabel = null;
          followStream();
        } else if (chunk.kind === 'tool-start') {
          liveSteps = [
            ...liveSteps,
            {
              id: chunk.id,
              name: chunk.name,
              label: chunk.label,
              ok: false,
              durationMs: 0,
              pending: true
            }
          ];
          activeToolLabel = chunk.label;
          followStream();
        } else if (chunk.kind === 'tool-end') {
          liveSteps = liveSteps.map((step) =>
            step.id === chunk.id
              ? { ...step, ok: chunk.ok, durationMs: chunk.durationMs, pending: false }
              : step
          );
          if (liveSteps.every((step) => !step.pending)) activeToolLabel = null;
        } else if (chunk.kind === 'done') {
          // Keep the local id as the key. Swapping in the server's UUID would
          // change the {#each} key, tearing down the message and re-rendering
          // its markdown from scratch — a visible flash right at the end.
          messages[replyIndex] = { ...chunk.message, id: messages[replyIndex].id };
        } else if (chunk.kind === 'error') {
          errorMessage = chunk.message;
          if (!messages[replyIndex].content) messages = messages.slice(0, replyIndex);
        }
      },
      { signal: abortController.signal }
    );

    abortController = null;
    streaming = false;
    activeToolLabel = null;
    if (stickToBottom) await scrollToBottom();
  }

  async function retry() {
    if (!lastQuestion || streaming) return;
    errorMessage = null;
    await send(lastQuestion);
  }

  async function copyMessage(message: TutorMessage) {
    if (!browser) return;
    try {
      await navigator.clipboard.writeText(message.content);
      copiedId = message.id;
      setTimeout(() => {
        if (copiedId === message.id) copiedId = null;
      }, 1400);
    } catch {
      /* clipboard can be blocked; silently skip */
    }
  }

  async function clearThread() {
    if (!services || streaming) return;
    await services.tutorService.clearConversation(trackSlug, problemSlug);
    messages = [];
    liveSteps = [];
    errorMessage = null;
    lastQuestion = '';
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

  /**
   * Steps to show under a message: the saved ones once the turn is persisted,
   * the live ones while it is still streaming. Saved steps are checked first
   * so the list doesn't blink empty in the gap between the `done` chunk and
   * `streaming` going false.
   */
  function stepsFor(message: TutorMessage, index: number): RenderStep[] {
    if (message.steps?.length) {
      return message.steps.map((step) => ({ ...step, pending: false }));
    }
    const isStreamingReply = streaming && index === messages.length - 1;
    return isStreamingReply ? liveSteps : [];
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

    <div class="tutor-scope">
      <span class="tutor-scope-title">{problemTitle}</span>
      {#if config?.enabled}
        <span class="tutor-scope-note">
          {#if isCoding}
            Can read this module, your code, runs, and submissions
          {:else}
            Can read this module's material
          {/if}
        </span>
      {/if}
    </div>

    <div class="tutor-scroll" bind:this={scrollBox} onscroll={onScroll}>
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
          <p class="tutor-empty-lead">Ask about anything on this page.</p>
          <p>
            {#if isCoding}
              The tutor can pull up this module's theory and tips, read the code in your
              editor, and check why your last run or submission failed — you don't need to
              paste anything.
            {:else}
              The tutor can pull up this module's theory and tips as it needs them.
            {/if}
            It will nudge you toward the answer rather than hand it over.
          </p>
        </div>
      {/if}

      {#each messages as message, i (message.id)}
        {@const steps = stepsFor(message, i)}
        <div class="tutor-message" class:tutor-message-user={message.role === 'user'}>
          <div class="tutor-message-head">
            <span class="tutor-role">{message.role === 'user' ? 'You' : 'Tutor'}</span>
            {#if message.role === 'assistant' && message.content && !(streaming && i === messages.length - 1)}
              <button
                class="tutor-copy"
                onclick={() => void copyMessage(message)}
                title="Copy this reply"
              >{copiedId === message.id ? 'Copied' : 'Copy'}</button>
            {/if}
          </div>

          {#if steps.length > 0}
            <ul class="tutor-steps">
              {#each steps as step (step.id)}
                <li class="tutor-step" class:tutor-step-failed={!step.pending && !step.ok}>
                  <span class="tutor-step-mark">
                    {#if step.pending}⋯{:else if step.ok}✓{:else}!{/if}
                  </span>
                  <span class="tutor-step-label">{step.label}</span>
                </li>
              {/each}
            </ul>
          {/if}

          {#if message.role === 'user'}
            <p class="tutor-user-text">{message.content}</p>
          {:else if message.content}
            <div class="tutor-markdown">
              <MarkdownRenderer
                content={message.content}
                variant="compact"
                headingPrefix="tutor"
                streaming={streaming && i === messages.length - 1}
              />
            </div>
          {:else if activeToolLabel}
            <span class="tutor-working">{activeToolLabel}…</span>
          {:else if streaming && i === messages.length - 1}
            <span class="tutor-typing" aria-label="Tutor is thinking">●●●</span>
          {:else}
            <!-- Not streaming and still empty: the turn ended without a reply.
                 Never leave the thinking dots up, or it looks like a hang. -->
            <span class="tutor-working">No answer came back. Try asking again.</span>
          {/if}
        </div>
      {/each}

      {#if errorMessage}
        <div class="tutor-error">
          <p>{errorMessage}</p>
          {#if lastQuestion}
            <button class="tutor-retry" onclick={() => void retry()} disabled={streaming}>
              Try again
            </button>
          {/if}
        </div>
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
        <textarea
          bind:this={textarea}
          bind:value={input}
          onkeydown={onKeydown}
          oninput={autoGrow}
          placeholder="Ask about this module…  (Enter to send, Shift+Enter for a new line)"
          rows="2"
        ></textarea>
        <div class="tutor-composer-actions">
          <span class="tutor-composer-hint">
            {#if streaming}Working…{:else}Ctrl+I toggles this panel{/if}
          </span>
          {#if streaming}
            <button class="tutor-send tutor-stop" onclick={stopStream}>Stop</button>
          {:else}
            <button class="tutor-send" onclick={() => void send()} disabled={!canSend}>
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
    min-width: 320px;
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
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    padding: 0.4rem 0.75rem 0.45rem;
    border-bottom: 1px solid #1e293b;
    flex-shrink: 0;
  }
  .tutor-scope-title {
    color: #94a3b8;
    font-size: 0.72rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .tutor-scope-note {
    color: #4b5b70;
    font-size: 0.65rem;
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
  .tutor-empty-lead {
    color: #cbd5e1;
    font-weight: 600;
    margin-bottom: 0.3rem;
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
  .tutor-message-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    min-height: 1rem;
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
  .tutor-copy {
    border: none;
    background: transparent;
    color: #475569;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    cursor: pointer;
    padding: 0 0.15rem;
    opacity: 0;
    transition: opacity 0.12s, color 0.12s;
  }
  .tutor-message:hover .tutor-copy,
  .tutor-copy:focus-visible {
    opacity: 1;
  }
  .tutor-copy:hover {
    color: #94a3b8;
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

  .tutor-steps {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    margin: 0 0 0.15rem;
    padding: 0.35rem 0.5rem;
    list-style: none;
    border-left: 2px solid #24344d;
    background: #121722;
    border-radius: 0 4px 4px 0;
  }
  .tutor-step {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    color: #64748b;
    font-size: 0.68rem;
    line-height: 1.5;
  }
  .tutor-step-mark {
    color: #3f8f5f;
    font-size: 0.62rem;
    width: 0.7rem;
    flex-shrink: 0;
  }
  .tutor-step-failed .tutor-step-mark {
    color: #b45309;
  }
  .tutor-step-failed .tutor-step-label {
    color: #a16207;
  }

  .tutor-working {
    color: #64748b;
    font-size: 0.75rem;
    font-style: italic;
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
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.4rem;
  }
  .tutor-retry {
    padding: 0.2rem 0.6rem;
    border: 1px solid #991b1b;
    border-radius: 4px;
    background: transparent;
    color: #fca5a5;
    font-size: 0.7rem;
    font-weight: 600;
    cursor: pointer;
  }
  .tutor-retry:hover:not(:disabled) {
    background: #451414;
  }
  .tutor-retry:disabled {
    opacity: 0.4;
    cursor: not-allowed;
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
  .tutor-composer textarea {
    width: 100%;
    resize: none;
    overflow-y: auto;
    max-height: 200px;
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
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }
  .tutor-composer-hint {
    color: #3f4b5e;
    font-size: 0.65rem;
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
