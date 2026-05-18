<script lang="ts">
  /**
   * StudyTimeTracker
   *
   * Invisible companion component that records how long the user actively
   * spends on a problem page. Mount once per problem with:
   *
   *   {#key problemId}
   *     <StudyTimeTracker {problemId} />
   *   {/key}
   *
   * The `{#key}` block is important: when the user navigates to another
   * problem, we want to END the current session (with a final flush) and
   * START a fresh one with a new UUID. Re-keying the component is the
   * simplest way to get that behaviour for free.
   *
   * Engagement model:
   *   - "Active" = the tab is visible AND there has been pointer/keyboard
   *     input within the last 25 minutes.
   *   - Every 5 s we add 5 s to `activeMs` if the user is active.
   *   - Every 30 s we post a heartbeat with the running total.
   *   - When the tab becomes hidden we flush immediately so the server has
   *     the latest count even if the user closes the tab.
   *   - On unload we use `sendBeacon` (with a `fetch keepalive` fallback)
   *     because the page may be gone before a normal fetch resolves.
   *
   * The idle modal:
   *   When the user crosses the 25-minute idle threshold, we open a small
   *   "Are you still there?" dialog. "Yes, I'm here" resumes tracking;
   *   "Don't ask again" suppresses the prompt for the rest of the page
   *   load (state lives in memory only — a fresh page load restores the
   *   safety net).
   */
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';

  interface Props {
    problemId: string;
    enabled?: boolean;
  }

  let { problemId, enabled = true }: Props = $props();

  // ── Constants ─────────────────────────────────────────────────────────
  const TICK_MS = 5000;
  const HEARTBEAT_MS = 30000;
  const IDLE_THRESHOLD_MS = 25 * 60 * 1000;
  const ACTIVITY_THROTTLE_MS = 250;
  const HEARTBEAT_URL = '/api/study-time/heartbeat';

  // ── Per-session state ─────────────────────────────────────────────────
  let sessionId = '';
  let startedAt = 0;
  let activeMs = 0;
  let lastActivityAt = 0;
  let lastActivityRegisteredAt = 0;
  let lastHeartbeatSentAt = 0;

  // ── Modal state ───────────────────────────────────────────────────────
  let idleModalOpen = $state(false);
  let dontAskThisSession = $state(false);

  // ── Intervals / listeners ─────────────────────────────────────────────
  let tickHandle: ReturnType<typeof setInterval> | null = null;
  let heartbeatHandle: ReturnType<typeof setInterval> | null = null;
  let activityHandler: (() => void) | null = null;
  let visibilityHandler: (() => void) | null = null;
  let pagehideHandler: (() => void) | null = null;

  // ── Helpers ───────────────────────────────────────────────────────────

  function genSessionId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    // Fallback: timestamp + random. Good enough for a single-user local
    // app where collisions are practically impossible.
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

  function postHeartbeat() {
    if (!browser) return;
    const payload = JSON.stringify({ sessionId, problemId, activeMs, startedAt });
    lastHeartbeatSentAt = Date.now();
    void fetch(HEARTBEAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload
    }).catch(() => {
      // Best-effort: the next heartbeat carries the same running total.
    });
  }

  /**
   * Final-flush variant used on unload / tab close. `sendBeacon` is the
   * only API guaranteed to fire during a navigation; we fall back to a
   * `keepalive` fetch when it isn't available (older or non-standard
   * environments).
   */
  function flushBeacon() {
    if (!browser) return;
    const payload = JSON.stringify({ sessionId, problemId, activeMs, startedAt });
    try {
      if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
        const blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon(HEARTBEAT_URL, blob);
        return;
      }
    } catch {
      // fall through to fetch
    }
    try {
      void fetch(HEARTBEAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true
      });
    } catch {
      // Last-resort: swallow. Nothing else we can do mid-unload.
    }
  }

  function registerActivity() {
    const now = Date.now();
    if (now - lastActivityRegisteredAt < ACTIVITY_THROTTLE_MS) return;
    lastActivityRegisteredAt = now;
    lastActivityAt = now;
    // A real interaction always implicitly answers the "still there?"
    // prompt, so close the modal if it's open.
    if (idleModalOpen) idleModalOpen = false;
  }

  function tick() {
    if (typeof document === 'undefined') return;
    if (document.hidden) return;
    const now = Date.now();
    const sinceActivity = now - lastActivityAt;
    if (sinceActivity > IDLE_THRESHOLD_MS) {
      // Idle: don't accumulate time. Open the prompt if appropriate.
      if (!idleModalOpen && !dontAskThisSession) {
        idleModalOpen = true;
      }
      return;
    }
    activeMs += TICK_MS;
  }

  function sendHeartbeatTick() {
    postHeartbeat();
  }

  function onVisibilityChange() {
    if (typeof document === 'undefined') return;
    if (document.hidden) {
      // Flush immediately so the server has the latest counter in case the
      // user closes the tab.
      postHeartbeat();
    }
  }

  function onPagehide() {
    flushBeacon();
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────

  onMount(() => {
    if (!browser || !enabled) return;

    sessionId = genSessionId();
    startedAt = Date.now();
    activeMs = 0;
    lastActivityAt = Date.now();
    lastActivityRegisteredAt = 0;

    // Initial heartbeat so the row exists from the get-go. Even if the user
    // hard-closes the tab seconds later we'll have a record.
    postHeartbeat();

    activityHandler = () => registerActivity();
    const evts: (keyof WindowEventMap)[] = [
      'mousemove',
      'keydown',
      'scroll',
      'click',
      'touchstart'
    ];
    for (const ev of evts) {
      window.addEventListener(ev, activityHandler, { passive: true });
    }

    visibilityHandler = onVisibilityChange;
    document.addEventListener('visibilitychange', visibilityHandler);

    pagehideHandler = onPagehide;
    window.addEventListener('pagehide', pagehideHandler);

    tickHandle = setInterval(tick, TICK_MS);
    heartbeatHandle = setInterval(sendHeartbeatTick, HEARTBEAT_MS);
  });

  onDestroy(() => {
    if (!browser) return;

    if (tickHandle !== null) clearInterval(tickHandle);
    if (heartbeatHandle !== null) clearInterval(heartbeatHandle);

    if (activityHandler) {
      const evts: (keyof WindowEventMap)[] = [
        'mousemove',
        'keydown',
        'scroll',
        'click',
        'touchstart'
      ];
      for (const ev of evts) window.removeEventListener(ev, activityHandler);
    }
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler);
    }
    if (pagehideHandler) {
      window.removeEventListener('pagehide', pagehideHandler);
    }

    // Final flush on unmount (covers navigation that doesn't fire pagehide).
    if (sessionId) flushBeacon();
  });

  // ── Idle modal actions ────────────────────────────────────────────────

  function handleStillHere() {
    lastActivityAt = Date.now();
    idleModalOpen = false;
  }

  function handleDontAsk() {
    dontAskThisSession = true;
    idleModalOpen = false;
    // NOTE: deliberately do NOT touch `lastActivityAt`. Time stays paused
    // until the user actually interacts with the page again.
  }
</script>

{#if idleModalOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="stt-backdrop">
    <div class="stt-card" role="dialog" tabindex="-1" aria-modal="true" aria-labelledby="stt-title">
      <h2 id="stt-title" class="stt-title">Are you still there?</h2>
      <p class="stt-body">
        We've paused your study timer. Tap a button below or click anywhere on the page to resume.
      </p>
      <div class="stt-actions">
        <button class="btn-ghost" onclick={handleDontAsk}>Don't ask again</button>
        <button class="btn-primary" onclick={handleStillHere}>Yes, I'm here</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .stt-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    animation: stt-fade 150ms ease-out;
  }
  .stt-card {
    width: 100%;
    max-width: 420px;
    background: #131720;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.55);
    animation: stt-rise 180ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .stt-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.5rem;
    letter-spacing: -0.005em;
  }
  .stt-body {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.5;
    margin: 0 0 1.1rem;
  }
  .stt-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
  }
  @keyframes stt-fade {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  @keyframes stt-rise {
    from { opacity: 0; transform: translateY(2px) scale(0.995); }
    to   { opacity: 1; transform: translateY(0)    scale(1);    }
  }
</style>
