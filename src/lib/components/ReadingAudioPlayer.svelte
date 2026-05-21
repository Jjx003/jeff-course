<script lang="ts">
  import { browser } from '$app/environment';
  import { onDestroy } from 'svelte';
  import type { ReadingAudioClip } from '$lib/types/audio.js';

  interface Props {
    clips: ReadingAudioClip[];
    activeIndex?: number;
    syncToActiveIndex?: boolean;
    compact?: boolean;
    storageKey?: string;
    onClipChange?: (clip: ReadingAudioClip, index: number) => void;
    onWordChange?: (clip: ReadingAudioClip, clipIndex: number, wordIndex: number) => void;
    onAdvance?: (index: number) => void;
  }

  let {
    clips,
    activeIndex = 0,
    syncToActiveIndex = false,
    compact = false,
    storageKey,
    onClipChange,
    onWordChange,
    onAdvance
  }: Props = $props();

  let audio = $state<HTMLAudioElement | undefined>(undefined);
  let currentIndex = $state(0);
  let isPlaying = $state(false);
  let isLoading = $state(false);
  let autoAdvance = $state(false);
  let playbackRate = $state(1);
  let status = $state('');
  let currentTimeMs = $state(0);
  let audioDurationMs = $state(0);
  let stubTimer: number | null = null;
  let stubStartedAt = 0;
  let stubDurationMs = 0;
  let animationFrame: number | null = null;
  let utterance: SpeechSynthesisUtterance | null = null;
  let lastNotifiedWordKey = '';
  let hasEndedCurrentClip = $state(false);
  let detailsOpen = $state(false);
  let restoredKey = '';
  let restoredClipId = $state<string | null>(null);
  let pendingSeekMs: number | null = null;
  let lastPersistedAt = 0;

  let currentClip = $derived(clips[currentIndex] ?? null);
  let nextClip = $derived(clips[currentIndex + 1] ?? null);
  let hasRealAudio = $derived(clips.some((clip) => clip.url));
  let hasCurrentRealAudio = $derived(Boolean(currentClip?.url));
  let hasClips = $derived(clips.length > 0);
  let canGoPrevious = $derived(currentIndex > 0);
  let canGoNext = $derived(currentIndex < clips.length - 1);
  let durationMs = $derived(
    Math.max(0, audioDurationMs || currentClip?.durationMs || currentClip?.words?.at(-1)?.endMs || 0)
  );
  let progressPercent = $derived(durationMs > 0 ? Math.min(100, (currentTimeMs / durationMs) * 100) : 0);
  let remainingMs = $derived(Math.max(0, durationMs - currentTimeMs));
  let label = $derived(hasRealAudio ? 'Audio reader' : 'Browser narration reader');
  let hasWordSync = $derived(Boolean(currentClip?.words?.length));
  let activeWordIndex = $derived.by(() => {
    const words = currentClip?.words ?? [];
    if (!words.length) return -1;
    const exact = words.findIndex((word) => currentTimeMs >= word.startMs && currentTimeMs < word.endMs);
    if (exact !== -1) return exact;
    if (currentTimeMs >= words.at(-1)!.endMs) return words.length - 1;
    return -1;
  });
  let activeTranscript = $derived.by(() => {
    const words = currentClip?.words ?? [];
    if (!words.length || activeWordIndex < 0) return currentClip?.text?.slice(0, 140) ?? '';
    const start = Math.max(0, activeWordIndex - 5);
    const end = Math.min(words.length, activeWordIndex + 9);
    return words
      .slice(start, end)
      .map((word, index) => (start + index === activeWordIndex ? ` ${word.text} ` : word.text))
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
  });

  $effect(() => {
    if (!syncToActiveIndex || clips.length === 0) return;
    const nextIndex = clampIndex(activeIndex);
    if (nextIndex === currentIndex) return;
    selectClip(nextIndex, isPlaying);
  });

  $effect(() => {
    if (clips.length === 0) {
      pause();
      currentIndex = 0;
      currentTimeMs = 0;
      audioDurationMs = 0;
      status = '';
      return;
    }
    if (currentIndex >= clips.length) selectClip(clips.length - 1, false);
  });

  $effect(() => {
    const clip = currentClip;
    const key = clip ? `${clip.id}:${currentIndex}:${activeWordIndex}` : 'none';
    if (key === lastNotifiedWordKey) return;
    lastNotifiedWordKey = key;
    if (clip) onWordChange?.(clip, currentIndex, activeWordIndex);
  });

  $effect(() => {
    if (audio) audio.playbackRate = playbackRate;
  });

  $effect(() => {
    const clipKey = clips.map((clip) => clip.id).join('|');
    const restoreKey = `${storageKey ?? ''}:${clipKey}`;
    if (!browser || !storageKey || clips.length === 0 || restoredKey === restoreKey) return;
    restoredKey = restoreKey;
    try {
      const saved = JSON.parse(localStorage.getItem(audioStorageKey()) ?? 'null') as {
        clipId?: string;
        timeMs?: number;
        playbackRate?: number;
        autoAdvance?: boolean;
      } | null;
      if (!saved) return;
      const index = clips.findIndex((clip) => clip.id === saved.clipId);
      if (index !== -1) currentIndex = index;
      currentTimeMs = Math.max(0, saved.timeMs ?? 0);
      pendingSeekMs = currentTimeMs;
      restoredClipId = saved.clipId ?? null;
      if ([0.75, 1, 1.25, 1.5].includes(saved.playbackRate ?? 0)) playbackRate = saved.playbackRate!;
      if (typeof saved.autoAdvance === 'boolean') autoAdvance = saved.autoAdvance;
      notifyClipChange();
    } catch {
      // Stored position is a convenience only.
    }
  });

  function clampIndex(index: number) {
    return Math.max(0, Math.min(clips.length - 1, index));
  }

  function notifyClipChange() {
    const clip = clips[currentIndex];
    if (clip) onClipChange?.(clip, currentIndex);
  }

  function audioStorageKey() {
    return `jeff-course:reading-audio:${storageKey}`;
  }

  function persistPosition(force = false) {
    if (!browser || !storageKey || !currentClip) return;
    const now = Date.now();
    if (!force && now - lastPersistedAt < 1500) return;
    lastPersistedAt = now;
    localStorage.setItem(
      audioStorageKey(),
      JSON.stringify({
        clipId: currentClip.id,
        timeMs: Math.max(0, Math.min(currentTimeMs, durationMs || currentTimeMs)),
        playbackRate,
        autoAdvance
      })
    );
  }

  function resetPlaybackPosition() {
    currentTimeMs = 0;
    audioDurationMs = 0;
    if (audio) audio.currentTime = 0;
    hasEndedCurrentClip = false;
  }

  function clearAnimationFrame() {
    if (animationFrame !== null) window.cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }

  function updateCurrentTimeFromAudio() {
    currentTimeMs = Math.round((audio?.currentTime ?? 0) * 1000);
    if (audio?.duration && Number.isFinite(audio.duration)) {
      audioDurationMs = Math.round(audio.duration * 1000);
    }
    persistPosition();
  }

  function updateStubTime() {
    if (!stubStartedAt || !stubDurationMs) return;
    currentTimeMs = Math.min(stubDurationMs, Math.round((performance.now() - stubStartedAt) * playbackRate));
    persistPosition();
  }

  function tickPlayback() {
    if (hasCurrentRealAudio) updateCurrentTimeFromAudio();
    else updateStubTime();

    if (isPlaying) animationFrame = window.requestAnimationFrame(tickPlayback);
  }

  function startClock() {
    clearAnimationFrame();
    if (browser) animationFrame = window.requestAnimationFrame(tickPlayback);
  }

  function clearStub() {
    if (stubTimer) window.clearTimeout(stubTimer);
    stubTimer = null;
    stubStartedAt = 0;
    stubDurationMs = 0;
    if (utterance && browser && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    utterance = null;
  }

  function pause() {
    isPlaying = false;
    isLoading = false;
    audio?.pause();
    clearAnimationFrame();
    clearStub();
  }

  async function playCurrent({ restart = false } = {}) {
    const clip = currentClip;
    if (!clip || isLoading) return;

    clearAnimationFrame();
    clearStub();
    status = '';
    isPlaying = true;
    hasEndedCurrentClip = false;
    notifyClipChange();

    if (clip.url && audio) {
      if (audio.src !== new URL(clip.url, window.location.href).href) {
        audio.src = clip.url;
        audioDurationMs = 0;
      }
      audio.playbackRate = playbackRate;
      if (restart) audio.currentTime = 0;
      else if (pendingSeekMs !== null || currentTimeMs > 0) {
        audio.currentTime = (pendingSeekMs ?? currentTimeMs) / 1000;
        pendingSeekMs = null;
      }
      isLoading = true;
      try {
        await audio.play();
        isLoading = false;
        updateCurrentTimeFromAudio();
        startClock();
      } catch {
        isPlaying = false;
        isLoading = false;
        status = 'Playback was blocked by the browser.';
      }
      return;
    }

    status = browser && 'speechSynthesis' in window ? 'Using browser narration.' : 'Previewing narration timing.';
    stubDurationMs = Math.max(3000, Math.min(30_000, durationMs || clip.durationMs || 7000));
    stubStartedAt = performance.now() - (restart ? 0 : currentTimeMs / playbackRate);
    startClock();

    if (browser && 'speechSynthesis' in window && clip.text) {
      utterance = new SpeechSynthesisUtterance(clip.text);
      utterance.rate = playbackRate;
      utterance.onend = () => handleEnded();
      utterance.onerror = () => handleEnded();
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }

    const remainingMs = Math.max(250, (stubDurationMs - currentTimeMs) / playbackRate);
    stubTimer = window.setTimeout(() => handleEnded(), remainingMs);
  }

  function togglePlay() {
    if (isPlaying) {
      pause();
      return;
    }
    void playCurrent();
  }

  function selectClip(index: number, autoplay = isPlaying) {
    const nextIndex = clampIndex(index);
    pause();
    currentIndex = nextIndex;
    resetPlaybackPosition();
    status = '';
    notifyClipChange();
    persistPosition(true);
    if (autoplay) void playCurrent({ restart: true });
  }

  function goToNextClip(autoplay = false) {
    if (!canGoNext) return;
    selectClip(currentIndex + 1, autoplay);
    onAdvance?.(currentIndex);
  }

  function cyclePlaybackRate() {
    const rates = [0.75, 1, 1.25, 1.5];
    const currentRateIndex = rates.indexOf(playbackRate);
    playbackRate = rates[(currentRateIndex + 1) % rates.length];
    persistPosition(true);
    if (isPlaying && !hasCurrentRealAudio) {
      clearStub();
      void playCurrent();
    }
  }

  function seekToPercent(value: number) {
    const nextTimeMs = Math.round((Math.max(0, Math.min(100, value)) / 100) * durationMs);
    currentTimeMs = nextTimeMs;
    if (audio && hasCurrentRealAudio) audio.currentTime = nextTimeMs / 1000;
    persistPosition(true);
    if (isPlaying && !hasCurrentRealAudio) {
      clearStub();
      void playCurrent();
    }
  }

  function handleProgressInput(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    seekToPercent(Number(input.value));
  }

  function handleEnded() {
    clearAnimationFrame();
    clearStub();
    currentTimeMs = durationMs;
    hasEndedCurrentClip = true;
    if (canGoNext && autoAdvance) {
      goToNextClip(true);
    } else {
      isPlaying = false;
      isLoading = false;
      status = canGoNext ? 'Checkpoint reached. Take a breath, then continue when ready.' : 'End of narration.';
      if (!canGoNext) onAdvance?.(currentIndex);
    }
    persistPosition(true);
  }

  function handleTimeUpdate() {
    updateCurrentTimeFromAudio();
  }

  function handleLoadedMetadata() {
    updateCurrentTimeFromAudio();
  }

  function formatTime(ms: number) {
    if (!ms || ms < 0) return '0:00';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  onDestroy(() => {
    persistPosition(true);
    pause();
  });
</script>

{#if hasClips}
  <section class="audio-player" class:stub={!hasRealAudio} class:compact aria-label={label}>
    <audio
      bind:this={audio}
      onended={handleEnded}
      onloadedmetadata={handleLoadedMetadata}
      ontimeupdate={handleTimeUpdate}
      onwaiting={() => (isLoading = true)}
      onplaying={() => (isLoading = false)}
      preload="metadata"
    ></audio>

    <div class="audio-main">
      <button
        type="button"
        class="transport-button primary"
        onclick={togglePlay}
        disabled={!currentClip || isLoading}
        aria-label={isPlaying ? 'Pause narration' : 'Play narration'}
        title={isPlaying ? 'Pause narration' : 'Play narration'}
      >
        {#if isLoading}
          <span class="spinner" aria-hidden="true"></span>
        {:else if isPlaying}
          <span aria-hidden="true">II</span>
        {:else}
          <span aria-hidden="true">Play</span>
        {/if}
      </button>

      <div class="audio-copy">
        <div class="audio-kicker">{hasRealAudio ? 'Listen along' : 'Browser narration'}</div>
        <div class="audio-title">{currentClip?.title ?? 'No clip selected'}</div>
        <div class="audio-sub">
          <span>Section {currentIndex + 1} of {clips.length}</span>
          <span>{formatTime(remainingMs)} left</span>
          {#if hasWordSync}
            <span>word sync on</span>
          {:else}
            <span>section sync only</span>
          {/if}
          {#if restoredClipId === currentClip?.id && currentTimeMs > 3000}
            <span>resumed</span>
          {/if}
        </div>
      </div>

      <div class="nav-controls" aria-label="Clip navigation">
        <button
          type="button"
          class="icon-button"
          onclick={() => selectClip(currentIndex - 1)}
          disabled={!canGoPrevious || isLoading}
          aria-label="Previous clip"
          title="Previous clip"
        >
          <span aria-hidden="true">Prev</span>
        </button>
        <button
          type="button"
          class="icon-button"
          onclick={() => goToNextClip(isPlaying)}
          disabled={!canGoNext || isLoading}
          aria-label="Next clip"
          title="Next clip"
        >
          <span aria-hidden="true">Next</span>
        </button>
      </div>
    </div>

    <div class="progress-row">
      <span class="time-label">{formatTime(currentTimeMs)}</span>
      <input
        class="progress-input"
        type="range"
        min="0"
        max="100"
        step="0.1"
        value={progressPercent}
        oninput={handleProgressInput}
        disabled={!currentClip || durationMs <= 0 || isLoading}
        aria-label="Narration progress"
        style={`--progress: ${progressPercent}%`}
      />
      <span class="time-label">{formatTime(durationMs)}</span>
    </div>

    {#if compact && (activeTranscript || currentClip)}
      <button
        type="button"
        class="transcript-peek"
        class:open={detailsOpen}
        onclick={() => (detailsOpen = !detailsOpen)}
        aria-expanded={detailsOpen}
      >
        <span>{hasWordSync ? 'Now reading' : 'Current section'}</span>
        <strong>{activeTranscript || currentClip?.title}</strong>
      </button>
    {/if}

    {#if status}
      <div class="audio-status" role="status">
        <span>{status}</span>
        {#if hasEndedCurrentClip && canGoNext}
          <button type="button" onclick={() => goToNextClip(false)}>Continue to next section</button>
        {/if}
      </div>
    {/if}

    {#if !compact || detailsOpen}
    <div class="learning-controls" aria-label="Learning playback controls">
      <div class="control-group">
        <span>Pace</span>
        <button
          type="button"
          onclick={cyclePlaybackRate}
          title="Change playback speed"
          aria-label={`Playback speed ${playbackRate}x`}
        >
          {playbackRate}x
        </button>
      </div>

      <div class="control-group flow">
        <span>Flow</span>
        <button
          type="button"
          class:active={!autoAdvance}
          onclick={() => {
            autoAdvance = false;
            persistPosition(true);
          }}
          aria-pressed={!autoAdvance}
          title="Pause after each section"
        >
          Pause at checkpoints
        </button>
        <button
          type="button"
          class:active={autoAdvance}
          onclick={() => {
            autoAdvance = true;
            persistPosition(true);
          }}
          aria-pressed={autoAdvance}
          title="Automatically continue to the next section"
        >
          Auto-continue
        </button>
      </div>

      <button
        type="button"
        class="continue-button"
        onclick={() => goToNextClip(false)}
        disabled={!canGoNext || isLoading}
        title={nextClip ? `Move to ${nextClip.title}` : 'No next section'}
      >
        Next section
      </button>
    </div>
    {/if}

    {#if nextClip && !autoAdvance && (!compact || detailsOpen)}
      <div class="next-preview">Next: {nextClip.title}</div>
    {/if}
  </section>
{/if}

<style>
  .audio-player {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.9rem;
    border: 1px solid #263449;
    border-radius: 8px;
    background: #101827;
    box-shadow: 0 14px 32px rgba(2, 6, 23, 0.2);
  }

  .audio-player.stub {
    border-style: dashed;
  }

  .audio-player.compact {
    gap: 0.55rem;
    padding: 0.65rem 0.75rem;
    border-color: rgba(56, 189, 248, 0.28);
    background: rgba(16, 24, 39, 0.94);
    box-shadow: 0 10px 26px rgba(2, 6, 23, 0.24);
  }

  audio {
    display: none;
  }

  .audio-main {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 0.85rem;
  }

  .transport-button,
  .icon-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #334155;
    border-radius: 6px;
    background: #131720;
    color: #cbd5e1;
    font-size: 0.78rem;
    font-weight: 750;
    transition: background 140ms ease, border-color 140ms ease, color 140ms ease, opacity 140ms ease;
  }

  .transport-button:hover:not(:disabled),
  .icon-button:hover:not(:disabled) {
    border-color: #475569;
    background: #1e293b;
    color: #f8fafc;
  }

  .transport-button:disabled,
  .icon-button:disabled {
    cursor: not-allowed;
    opacity: 0.48;
  }

  .transport-button.primary {
    min-width: 64px;
    min-height: 40px;
    border-color: #0ea5e9;
    background: #0284c7;
    color: #f8fafc;
    font-size: 0.9rem;
  }

  .compact .transport-button.primary {
    min-width: 42px;
    min-height: 36px;
  }

  .transport-button.primary:hover:not(:disabled) {
    background: #0369a1;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(248, 250, 252, 0.35);
    border-top-color: #f8fafc;
    border-radius: 999px;
    animation: spin 720ms linear infinite;
  }

  .audio-copy {
    min-width: 0;
  }

  .audio-kicker {
    color: #67e8f9;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .audio-title {
    overflow: hidden;
    margin-top: 0.1rem;
    color: #e2e8f0;
    font-size: 0.9rem;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .compact .audio-kicker {
    display: none;
  }

  .compact .audio-title {
    font-size: 0.84rem;
  }

  .audio-sub {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.6rem;
    margin-top: 0.15rem;
    color: #94a3b8;
    font-size: 0.74rem;
    line-height: 1.35;
  }

  .nav-controls {
    display: flex;
    gap: 0.35rem;
  }

  .icon-button {
    min-width: 48px;
    min-height: 32px;
    padding: 0.3rem 0.55rem;
  }

  .compact .icon-button {
    min-width: 36px;
    min-height: 30px;
    padding: 0.25rem 0.45rem;
    font-size: 1rem;
  }

  .progress-row {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr) 42px;
    align-items: center;
    gap: 0.6rem;
  }

  .compact .progress-row {
    grid-template-columns: 36px minmax(0, 1fr) 36px;
    gap: 0.45rem;
  }

  .time-label {
    color: #94a3b8;
    font-variant-numeric: tabular-nums;
    font-size: 0.72rem;
    font-weight: 650;
    text-align: center;
  }

  .progress-input {
    width: 100%;
    height: 6px;
    accent-color: #38bdf8;
    cursor: pointer;
    border-radius: 999px;
    background: linear-gradient(90deg, #38bdf8 var(--progress), #1e293b var(--progress));
  }

  .progress-input:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }

  .audio-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.45rem 0.6rem;
    border: 1px solid #263449;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.55);
    color: #cbd5e1;
    font-size: 0.76rem;
    line-height: 1.4;
  }

  .audio-status button {
    flex-shrink: 0;
    min-height: 28px;
    padding: 0.25rem 0.55rem;
    border: 1px solid #0ea5e9;
    border-radius: 6px;
    background: rgba(14, 165, 233, 0.13);
    color: #e0f2fe;
    font-size: 0.72rem;
    font-weight: 750;
  }

  .transcript-peek {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    align-items: center;
    gap: 0.55rem;
    min-height: 30px;
    padding: 0.35rem 0.5rem;
    border: 1px solid #263449;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.46);
    text-align: left;
  }

  .transcript-peek:hover {
    border-color: #334155;
    background: rgba(30, 41, 59, 0.62);
  }

  .transcript-peek span {
    color: #67e8f9;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .transcript-peek strong {
    overflow: hidden;
    color: #cbd5e1;
    font-size: 0.76rem;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .transcript-peek.open strong {
    white-space: normal;
  }

  .learning-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.55rem;
    padding-top: 0.05rem;
  }

  .control-group {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    min-height: 34px;
    padding: 0.16rem;
    border: 1px solid #263449;
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.34);
  }

  .control-group > span {
    padding: 0 0.35rem;
    color: #94a3b8;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .learning-controls button {
    min-height: 32px;
    padding: 0.35rem 0.65rem;
    border: 1px solid #334155;
    border-radius: 6px;
    background: #131720;
    color: #cbd5e1;
    font-size: 0.76rem;
    font-weight: 750;
    transition: background 140ms ease, border-color 140ms ease, color 140ms ease;
  }

  .learning-controls button:hover:not(:disabled) {
    border-color: #475569;
    background: #1e293b;
    color: #f8fafc;
  }

  .learning-controls button.active {
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.14);
    color: #e0f2fe;
  }

  .learning-controls button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .continue-button {
    margin-left: auto;
  }

  .next-preview {
    overflow: hidden;
    color: #94a3b8;
    font-size: 0.74rem;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 720px) {
    .audio-main {
      grid-template-columns: auto minmax(0, 1fr);
    }

    .audio-player.compact .audio-main {
      grid-template-columns: auto minmax(0, 1fr) auto;
    }

    .nav-controls {
      grid-column: 1 / -1;
      justify-content: stretch;
    }

    .compact .nav-controls {
      grid-column: auto;
    }

    .icon-button {
      flex: 1;
    }

    .compact .icon-button {
      flex: 0 0 auto;
    }

    .control-group.flow {
      width: 100%;
      flex-wrap: wrap;
    }

    .continue-button {
      width: 100%;
      margin-left: 0;
    }

    .audio-status {
      align-items: stretch;
      flex-direction: column;
    }
  }
</style>
