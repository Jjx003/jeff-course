/**
 * Warm Python process pool.
 *
 * A pooled host is a `uv run … python infra/python/run_host.py` process that
 * has already imported torch (and friends) and is blocked on stdin waiting
 * for one script path. Handing a run to a warm host skips interpreter
 * startup, uv's requirement resolution, the torch import, and CUDA init —
 * the 3-10s of dead time every Run used to pay before the learner's first
 * line executed.
 *
 * Design constraints that shaped this:
 *
 *   - One run per host. The host exits afterwards and the pool starts a
 *     replacement in the background. Every run therefore still gets a fresh
 *     namespace, so stdout-diff grading stays exactly as sound as it was
 *     with the direct spawn path, and nothing leaks between users. Only
 *     sys.modules is reused, which is the part we actually wanted warm.
 *   - Warming never overlaps a run. Two concurrent `uv` invocations
 *     contend on the same cache, and on Windows that surfaces as
 *     "failed to remove directory … (os error 32)". Warms are scheduled
 *     from quiet moments (page load, post-run) with a short delay.
 *   - Warm hosts hold real memory (a torch import is ~300-500 MB RSS, more
 *     once transformers is in). The pool is capped and idle hosts are
 *     evicted, so a laptop doesn't quietly lose a gigabyte to a course it
 *     stopped studying an hour ago.
 *
 * The pool is best-effort throughout: if anything fails, callers fall back
 * to the direct spawn path and the learner sees a normal (if slower) run.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';

import { childEnv, prewarmModulesFor, requirementsKey } from './pyenv.js';
import { ensureVenv } from './venvs.js';

const IS_WINDOWS = process.platform === 'win32';

const READY_SENTINEL = '__JEFF_COURSE_HOST_READY__';

// ── Tunables ──────────────────────────────────────────────────────────────

function envInt(name: string, def: number): number {
  const raw = process.env[name];
  if (!raw) return def;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : def;
}

/** Set SANDBOX_POOL=0 to disable warm hosts entirely. */
const POOL_ENABLED = process.env.SANDBOX_POOL !== '0';
/** Distinct requirement sets kept warm at once. Each costs real RSS. */
const MAX_HOSTS = envInt('SANDBOX_POOL_MAX_HOSTS', 2);
/** Idle host lifetime. */
const IDLE_TTL_MS = envInt('SANDBOX_POOL_IDLE_MS', 15 * 60_000);
/** Ceiling on a single warm attempt — a cold torch install is genuinely slow. */
const WARM_TIMEOUT_MS = envInt('SANDBOX_POOL_WARM_TIMEOUT_MS', 10 * 60_000);
/** Settle time before warming, so we never race a run that just finished. */
const WARM_DELAY_MS = envInt('SANDBOX_POOL_WARM_DELAY_MS', 2_000);

function hostScriptPath(): string {
  return path.join(process.cwd(), 'infra', 'python', 'run_host.py');
}

// ── Pool state (on globalThis so HMR doesn't orphan processes) ────────────

export interface PoolSpec {
  /** Identity of the requirement set. Hosts are pooled per key. */
  key: string;
  requirementsPath?: string;
  prewarm: string[];
}

interface WarmHost {
  key: string;
  proc: ChildProcess;
  readyAt: number;
  idleTimer: NodeJS.Timeout | null;
}

interface PoolState {
  /** Ready hosts by key. At most one per key. */
  idle: Map<string, WarmHost>;
  /** In-flight warm attempts by key, so we never start two. */
  warming: Map<string, Promise<void>>;
  /** Keys whose warm attempt failed — don't retry in a loop. */
  failed: Set<string>;
  /** Hosts handed out and not yet finished. Blocks new warms. */
  busy: number;
  /** Pending scheduled warms, so a burst of requests coalesces. */
  scheduled: Map<string, NodeJS.Timeout>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
const STATE: PoolState = g.__sandboxPool ?? (g.__sandboxPool = {
  idle: new Map<string, WarmHost>(),
  warming: new Map<string, Promise<void>>(),
  failed: new Set<string>(),
  busy: 0,
  scheduled: new Map<string, NodeJS.Timeout>()
} satisfies PoolState);

// ── Spec construction ─────────────────────────────────────────────────────

/**
 * Pool identity for a module's requirement set. Modules that declare
 * byte-identical requirements share a host.
 */
export function specFor(requirementsPath: string | undefined): PoolSpec {
  return {
    key: requirementsKey(requirementsPath),
    ...(requirementsPath ? { requirementsPath } : {}),
    prewarm: prewarmModulesFor(requirementsPath)
  };
}

/**
 * Whether pooling is worth it for this spec. A module with no dependencies
 * starts in ~50ms anyway; keeping a host warm for it would spend memory to
 * save nothing.
 */
export function isPoolable(spec: PoolSpec): boolean {
  return POOL_ENABLED && spec.prewarm.length > 0 && existsSync(hostScriptPath());
}

// ── Acquire ───────────────────────────────────────────────────────────────

export interface AcquiredHost {
  proc: ChildProcess;
  /** How long this host had been warm, for the progress note. */
  warmForMs: number;
  /** Hand the script to the host. Call once, after attaching stream handlers. */
  dispatch: (scriptPath: string) => void;
  /** Mark the run finished so the pool may warm a replacement. */
  release: () => void;
}

/**
 * Take a ready host for `spec`, or null if none is warm. Never blocks and
 * never spawns — a cold cache means the caller runs directly and the pool
 * warms up afterwards for next time.
 */
export function acquire(spec: PoolSpec): AcquiredHost | null {
  if (!POOL_ENABLED) return null;
  const host = STATE.idle.get(spec.key);
  if (!host) return null;

  STATE.idle.delete(spec.key);
  if (host.idleTimer) clearTimeout(host.idleTimer);

  const { proc } = host;
  if (proc.exitCode !== null || proc.signalCode !== null) return null;

  // Detach our warm-phase listeners and park the streams so nothing is lost
  // between here and the caller attaching its own handlers. The host is
  // blocked on stdin and produces no output until dispatch(), so this
  // window is quiet by construction.
  proc.stdout?.removeAllListeners('data');
  proc.stderr?.removeAllListeners('data');
  proc.stdout?.pause();
  proc.stderr?.pause();
  proc.removeAllListeners('exit');
  proc.removeAllListeners('error');

  STATE.busy += 1;
  let released = false;

  return {
    proc,
    warmForMs: Date.now() - host.readyAt,
    dispatch: (scriptPath: string) => {
      try {
        proc.stdin?.write(`${JSON.stringify({ path: scriptPath, argv: [scriptPath] })}\n`);
        // Close stdin so user code reading from it sees EOF, matching the
        // direct path's `stdio: ['ignore', …]` (which is /dev/null).
        proc.stdin?.end();
      } catch {
        try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      }
    },
    release: () => {
      if (released) return;
      released = true;
      STATE.busy = Math.max(0, STATE.busy - 1);
    }
  };
}

// ── Warm ──────────────────────────────────────────────────────────────────

/**
 * Ask the pool to have a host ready for `spec`, eventually. Returns
 * immediately; the warm happens on a timer so it never overlaps an active
 * run (concurrent `uv` invocations contend on the cache — that is the
 * Windows "os error 32" failure mode).
 */
export function scheduleWarm(spec: PoolSpec): void {
  if (!isPoolable(spec)) return;
  if (STATE.idle.has(spec.key) || STATE.warming.has(spec.key)) return;
  if (STATE.failed.has(spec.key)) return;
  if (STATE.scheduled.has(spec.key)) return;

  const timer = setTimeout(() => {
    STATE.scheduled.delete(spec.key);
    if (STATE.busy > 0) {
      // A run started while we waited. Try again after it settles.
      scheduleWarm(spec);
      return;
    }
    void warm(spec).catch(() => { /* recorded in STATE.failed */ });
  }, WARM_DELAY_MS);

  // Don't hold the event loop open for a warm-up.
  timer.unref?.();
  STATE.scheduled.set(spec.key, timer);
}

async function warm(spec: PoolSpec): Promise<void> {
  if (STATE.idle.has(spec.key)) return;
  const inflight = STATE.warming.get(spec.key);
  if (inflight) return inflight;

  const promise = (async () => {
    evictBeyondCapacity();

    // Run the host out of a persistent venv rather than `uv run`. A warm
    // host is long-lived by design, and a long-lived process holding uv's
    // ephemeral environment open is exactly what breaks concurrent uv
    // operations on Windows. With a venv there is no uv process in the tree
    // at all once the install is done.
    const python = await ensureVenv(
      { key: spec.key, ...(spec.requirementsPath ? { requirementsPath: spec.requirementsPath } : {}) }
    );
    if (!python) throw new Error('no venv available for this requirement set');

    const proc = spawn(python, [hostScriptPath()], {
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: !IS_WINDOWS,
      windowsHide: true,
      env: childEnv({ JEFF_PREWARM: spec.prewarm.join(',') })
    });

    await waitForReady(proc);

    const host: WarmHost = { key: spec.key, proc, readyAt: Date.now(), idleTimer: null };
    host.idleTimer = setTimeout(() => evict(spec.key, 'idle'), IDLE_TTL_MS);
    host.idleTimer.unref?.();

    // If the host dies while parked (OOM, user killed it), forget it so the
    // next acquire() doesn't hand out a corpse.
    proc.on('exit', () => {
      const parked = STATE.idle.get(spec.key);
      if (parked?.proc === proc) {
        if (parked.idleTimer) clearTimeout(parked.idleTimer);
        STATE.idle.delete(spec.key);
      }
    });
    proc.on('error', () => { /* surfaced on exit */ });

    STATE.idle.set(spec.key, host);
  })().catch((err) => {
    // One failure per key is enough; a broken requirement set would
    // otherwise respawn uv forever in the background.
    STATE.failed.add(spec.key);
    console.warn('[sandbox] warm host failed for', spec.key, err instanceof Error ? err.message : err);
  }).finally(() => {
    STATE.warming.delete(spec.key);
  });

  STATE.warming.set(spec.key, promise);
  return promise;
}

/**
 * Resolve once the host prints its ready sentinel. Everything printed before
 * that (uv resolution chatter, import warnings) is discarded — no session is
 * attached yet, so it belongs to nobody.
 */
function waitForReady(proc: ChildProcess): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    let stderrTail = '';

    const cleanup = () => {
      clearTimeout(timer);
      proc.stdout?.removeListener('data', onStdout);
      proc.stderr?.removeListener('data', onStderr);
      proc.removeListener('exit', onExit);
      proc.removeListener('error', onError);
    };

    const succeed = () => {
      if (settled) return;
      settled = true;
      cleanup();
      proc.stdout?.pause();
      proc.stderr?.pause();
      resolve();
    };

    const fail = (err: Error) => {
      if (settled) return;
      settled = true;
      cleanup();
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      reject(err);
    };

    const onStdout = () => { /* drain; the host prints nothing here */ };
    const onStderr = (chunk: Buffer) => {
      stderrTail += chunk.toString();
      if (stderrTail.includes(READY_SENTINEL)) {
        succeed();
        return;
      }
      if (stderrTail.length > 16_384) stderrTail = stderrTail.slice(-4_096);
    };
    const onExit = (code: number | null) => {
      fail(new Error(`host exited with ${code} before ready: ${stderrTail.trim().slice(-400)}`));
    };
    const onError = (err: Error) => fail(err);

    const timer = setTimeout(() => fail(new Error('warm timed out')), WARM_TIMEOUT_MS);
    timer.unref?.();

    proc.stdout?.on('data', onStdout);
    proc.stderr?.on('data', onStderr);
    proc.on('exit', onExit);
    proc.on('error', onError);
  });
}

// ── Eviction ──────────────────────────────────────────────────────────────

function evict(key: string, reason: string): void {
  const host = STATE.idle.get(key);
  if (!host) return;
  STATE.idle.delete(key);
  if (host.idleTimer) clearTimeout(host.idleTimer);
  try {
    // The host is blocked on stdin; closing it lets run_host exit cleanly.
    host.proc.stdin?.end();
  } catch { /* ignore */ }
  setTimeout(() => {
    try { host.proc.kill('SIGKILL'); } catch { /* ignore */ }
  }, 1_000).unref?.();
  console.debug?.(`[sandbox] evicted warm host ${key} (${reason})`);
}

/** Drop the least-recently-warmed hosts until there's room for one more. */
function evictBeyondCapacity(): void {
  while (STATE.idle.size >= MAX_HOSTS) {
    let oldestKey: string | null = null;
    let oldestAt = Infinity;
    for (const [key, host] of STATE.idle) {
      if (host.readyAt < oldestAt) {
        oldestAt = host.readyAt;
        oldestKey = key;
      }
    }
    if (!oldestKey) return;
    evict(oldestKey, 'capacity');
  }
}

/** Tear every warm host down. Used by the boot hook and on shutdown. */
export function shutdownPool(): void {
  for (const key of [...STATE.idle.keys()]) evict(key, 'shutdown');
  for (const timer of STATE.scheduled.values()) clearTimeout(timer);
  STATE.scheduled.clear();
}

if (!g.__sandboxPoolExitHook) {
  g.__sandboxPoolExitHook = true;
  process.on('exit', () => shutdownPool());
}

// ── Diagnostics ───────────────────────────────────────────────────────────

export interface PoolSnapshot {
  enabled: boolean;
  maxHosts: number;
  idleKeys: string[];
  warmingKeys: string[];
  failedKeys: string[];
  busy: number;
}

export function poolSnapshot(): PoolSnapshot {
  return {
    enabled: POOL_ENABLED,
    maxHosts: MAX_HOSTS,
    idleKeys: [...STATE.idle.keys()],
    warmingKeys: [...STATE.warming.keys()],
    failedKeys: [...STATE.failed],
    busy: STATE.busy
  };
}
