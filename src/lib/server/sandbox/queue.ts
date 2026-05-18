/**
 * Per-mode FIFO queue with bounded concurrency.
 *
 * A docker job that takes 60s to load a model must not block a 200ms cpp
 * baremetal run; we therefore keep independent slot pools for each mode
 * group (baremetal / docker / docker-gpu).
 *
 * SERVER-SIDE ONLY.
 */

import type { SandboxMode } from './types.js';

type Job = () => Promise<void>;

interface QueueState {
  capacity: number;
  inflight: number;
  pending: { job: Job; resolve: () => void }[];
}

function envInt(name: string, def: number): number {
  const raw = process.env[name];
  if (!raw) return def;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : def;
}

// Tunable. Override via env if a host has lots of GPU memory and wants to
// stack runs, etc. The brief defaults are 2 baremetal, 2 docker, 1 docker-gpu.
const STATE: Record<SandboxMode, QueueState> = {
  baremetal: { capacity: envInt('SANDBOX_BAREMETAL_CONCURRENCY', 2), inflight: 0, pending: [] },
  docker: { capacity: envInt('SANDBOX_DOCKER_CONCURRENCY', 2), inflight: 0, pending: [] },
  'docker-gpu': { capacity: envInt('SANDBOX_DOCKER_GPU_CONCURRENCY', 1), inflight: 0, pending: [] }
};

export interface QueueSnapshot {
  mode: SandboxMode;
  capacity: number;
  inflight: number;
  pending: number;
}

export function queueSnapshot(): QueueSnapshot[] {
  return (Object.keys(STATE) as SandboxMode[]).map((mode) => ({
    mode,
    capacity: STATE[mode].capacity,
    inflight: STATE[mode].inflight,
    pending: STATE[mode].pending.length
  }));
}

/**
 * Submit a job for the given mode.
 *
 * Resolves immediately to a tuple of [waitForSlot, completion]:
 *   - waitForSlot resolves when the slot opens (sender can transition the
 *     session status from "queued" → "starting").
 *   - completion resolves when the underlying job finishes (sender can
 *     await this to know when to clean up).
 *
 * The two-phase API matters because the UI wants to render "queued" vs
 * "running" distinctly.
 */
export function submitJob(
  mode: SandboxMode,
  job: Job
): { waitForSlot: Promise<void>; completion: Promise<void>; isQueued: () => boolean; removeIfQueued: () => boolean } {
  const state = STATE[mode];
  if (!state) {
    return {
      waitForSlot: Promise.reject(new Error(`Unknown mode: ${mode}`)),
      completion: Promise.reject(new Error(`Unknown mode: ${mode}`)),
      isQueued: () => false,
      removeIfQueued: () => false
    };
  }

  // The job is wrapped so we always decrement inflight and drain the queue.
  let completionResolve!: () => void;
  let completionReject!: (err: unknown) => void;
  const completion = new Promise<void>((resolve, reject) => {
    completionResolve = resolve;
    completionReject = reject;
  });

  let slotResolve!: () => void;
  const waitForSlot = new Promise<void>((resolve) => {
    slotResolve = resolve;
  });

  const wrappedJob: Job = async () => {
    slotResolve();
    try {
      await job();
      completionResolve();
    } catch (err) {
      completionReject(err);
    } finally {
      state.inflight -= 1;
      drain(mode);
    }
  };

  // Pending entry kept so we can remove on cancel-while-queued.
  const pendingEntry = { job: wrappedJob, resolve: slotResolve };

  if (state.inflight < state.capacity) {
    state.inflight += 1;
    // Schedule on the microtask queue so callers see the return value first.
    queueMicrotask(() => {
      void wrappedJob();
    });
  } else {
    state.pending.push(pendingEntry);
  }

  return {
    waitForSlot,
    completion,
    isQueued: () => state.pending.includes(pendingEntry),
    removeIfQueued: () => {
      const idx = state.pending.indexOf(pendingEntry);
      if (idx === -1) return false;
      state.pending.splice(idx, 1);
      return true;
    }
  };
}

function drain(mode: SandboxMode): void {
  const state = STATE[mode];
  while (state.inflight < state.capacity && state.pending.length > 0) {
    const next = state.pending.shift()!;
    state.inflight += 1;
    queueMicrotask(() => {
      void next.job();
    });
  }
}
