/**
 * Sandbox orchestrator — public API consumed by the API routes.
 *
 *   startSession      — accept a job, queue it, kick off the runtime.
 *   listSessions      — DB-backed history + live state.
 *   getSession        — single record by id.
 *   cancelSession     — graceful stop (SIGTERM-equivalent / docker stop).
 *   killSession       — force kill (SIGKILL / docker kill -s KILL).
 *   subscribeToLogs   — register an SSE-style callback on a live session.
 *   queueSnapshot     — reports concurrency state for the header pill.
 *   submitResult      — produce a SubmitResult for the legacy /api/execute
 *                       shim by awaiting completion + diffing stdout.
 *
 * Resolution helpers (`resolveProblemContext`, etc) live here so the routes
 * stay thin.
 *
 * SERVER-SIDE ONLY.
 */

import { randomUUID } from 'node:crypto';
import { loadProblem } from '$lib/content/courseLoader.js';
import type { Problem } from '$lib/types/course.js';
import { gradeOutput } from '$lib/server/grading.js';
import { reapStaleSessionsOnBoot, insertSession, updateSession, listSessionRecords, getSessionById } from './persistence.js';
import * as registry from './registry.js';
import { submitJob, queueSnapshot } from './queue.js';
import type {
  LogChunk,
  ResourceLimits,
  SandboxMode,
  SessionRecord,
  StartSessionRequest
} from './types.js';
import { defaultResourcesFor, isTerminal } from './types.js';
import { runBaremetal, type RunOutcome } from './runtime/baremetal.js';
import * as pool from './runtime/pool.js';

// ── Boot-time housekeeping ────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
if (!g.__sandboxBootReaped) {
  g.__sandboxBootReaped = true;
  void (async () => {
    try {
      await reapStaleSessionsOnBoot();
    } catch (err) {
      console.warn('[sandbox] reapStaleSessionsOnBoot failed', err);
    }
    // Best-effort: tear down any leftover jeff-course containers from a
    // prior crash. The reaper soft-fails when docker isn't installed, so
    // we can call it unconditionally — no need to gate on a capability
    // probe (which itself spawns docker and would re-do the work).
    try {
      const { reapZombieContainers } = await import('./runtime/docker.js');
      const { removed, reason } = await reapZombieContainers();
      if (removed.length > 0) {
        console.info(`[sandbox] reaped ${removed.length} zombie container(s):`, removed.join(', '));
      } else if (reason) {
        // Quiet: this is expected on hosts without docker. The
        // `getCapabilities()` call surfaces the same info to users.
        console.debug?.('[sandbox] zombie-reap skipped:', reason);
      }
    } catch (err) {
      console.warn('[sandbox] reapZombieContainers failed', err);
    }
  })();
}

// ── Helpers ───────────────────────────────────────────────────────────────

function mergeResources(
  mode: SandboxMode,
  patch: Partial<ResourceLimits> | undefined
): ResourceLimits {
  const defaults = defaultResourcesFor(mode);
  if (!patch) return defaults;
  return {
    memoryMb: patch.memoryMb ?? defaults.memoryMb,
    cpus: patch.cpus ?? defaults.cpus,
    gpu: patch.gpu ?? defaults.gpu,
    timeoutMs: patch.timeoutMs ?? defaults.timeoutMs
  };
}

function resolveProblem(problemId: string): Problem | null {
  const [trackSlug, problemSlug] = problemId.split('/');
  if (!trackSlug || !problemSlug) return null;
  return loadProblem(trackSlug, problemSlug);
}

/**
 * Raise the requested limits to the module's own floor.
 *
 * Resource preferences are saved per *track* but the demands are per
 * *module*: a track's saved 60s (seeded by whichever exercise the learner
 * opened first) would otherwise kill a module that needs to load model
 * weights. The module hint can only raise limits, never lower them, so a
 * learner who deliberately grants more memory or time keeps it — and Cancel
 * is always available if a run turns out to be a mistake.
 */
function applyModuleFloors(
  resources: ResourceLimits,
  mode: SandboxMode,
  problem: Problem | null
): ResourceLimits {
  const hint = problem?.runtime?.resources;
  if (!hint) return resources;

  const out = { ...resources };
  if (typeof hint.timeoutMs === 'number' && hint.timeoutMs > out.timeoutMs) {
    out.timeoutMs = hint.timeoutMs;
  }
  // memoryMb is only enforced by the container runtimes; on baremetal 0
  // means "unlimited" and raising it would just be a misleading number.
  if (mode !== 'baremetal' && typeof hint.memoryMb === 'number' && hint.memoryMb > out.memoryMb) {
    out.memoryMb = hint.memoryMb;
  }
  return out;
}

// ── Public API ────────────────────────────────────────────────────────────

export interface StartSessionResult {
  id: string;
  queued: boolean;
}

/**
 * Submit a new session for execution. Returns immediately with the assigned
 * id; the caller can poll `/api/sessions/[id]` or open the SSE stream.
 */
export async function startSession(
  req: StartSessionRequest
): Promise<StartSessionResult> {
  const mode: SandboxMode = req.mode ?? 'baremetal';
  // Resolved up front (rather than inside the job) so the module's runtime
  // floors are reflected in the persisted row and in what the UI reads back.
  const problem = resolveProblem(req.problemId);
  const resources = applyModuleFloors(mergeResources(mode, req.resources), mode, problem);
  const id = randomUUID();
  const now = Date.now();

  const record: SessionRecord = {
    id,
    userId: req.userId,
    problemId: req.problemId,
    language: req.language,
    action: req.action,
    mode,
    status: 'queued',
    containerName: null,
    hostPid: null,
    startedAt: now,
    completedAt: null,
    exitCode: null,
    errorMessage: null,
    resources,
    stdoutBytes: 0,
    stderrBytes: 0
  };

  await insertSession(record);
  const entry = registry.createEntry(record);

  // The actual job — resolves to nothing; failures are written into the DB
  // and emitted to subscribers.
  const job = async () => {
    // We've now got a slot. Flip to "starting".
    if (entry.abort.signal.aborted) {
      await markCancelled(id, 'Cancelled while queued');
      return;
    }
    await transition(id, 'starting');
    registry.publish(id, { kind: 'status', status: 'starting' });

    if (!problem) {
      registry.publish(id, { kind: 'stderr', data: `Problem not found: ${req.problemId}\n` });
      await markFinal(id, 'failed', null, `Problem not found: ${req.problemId}`, 0, 0, now);
      return;
    }

    await transition(id, 'running');
    registry.publish(id, { kind: 'status', status: 'running' });

    let outcome: RunOutcome;
    try {
      if (mode === 'baremetal') {
        outcome = await runBaremetal({
          record: entry.record,
          code: req.code,
          requirementsPath: problem.requirementsPath,
          resources
        });
      } else if (mode === 'docker' || mode === 'docker-gpu') {
        // Lazy-loaded so failures inside docker code don't crash boot. If
        // the module isn't built or docker isn't available, we fall back
        // to baremetal with a visible banner — same path as host detection.
        try {
          const dockerMod = await import('./runtime/docker.js');
          outcome = await dockerMod.runDocker({
            record: entry.record,
            code: req.code,
            requirementsPath: problem.requirementsPath,
            resources,
            problem
          });
        } catch (importErr) {
          const msg = importErr instanceof Error ? importErr.message : String(importErr);
          registry.publish(id, {
            kind: 'stderr',
            data: `Container runtime unavailable (${msg}). Falling back to baremetal.\n`
          });
          // Note: we re-flag the mode in the live record so the UI sees
          // the actual execution path. Persisted row reflects original
          // request so history is accurate.
          outcome = await runBaremetal({
            record: entry.record,
            code: req.code,
            requirementsPath: problem.requirementsPath,
            resources
          });
        }
      } else {
        throw new Error(`Unknown mode: ${mode}`);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      registry.publish(id, { kind: 'stderr', data: `${msg}\n` });
      await markFinal(id, 'failed', null, msg, 0, msg.length, now);
      return;
    }

    let finalStatus: SessionRecord['status'] = 'completed';
    if (outcome.errorMessage === 'Cancelled') finalStatus = 'cancelled';
    else if (outcome.timedOut) finalStatus = 'killed';
    else if (outcome.exitCode !== 0) finalStatus = 'failed';

    // For submit actions, grade against expected_output and persist a
    // verdict alongside the row. The UI fetches the record after the SSE
    // exit event to surface the result.
    let submitVerdict: SessionRecord['submitVerdict'] = null;
    let submitMessage: string | null = null;
    let submitScore: number | null = null;
    if (req.action === 'submit') {
      const expected = problem.expectedOutput?.[req.language];
      if (finalStatus === 'cancelled') {
        submitVerdict = 'error';
        submitMessage = 'Submission cancelled.';
      } else if (finalStatus === 'killed') {
        submitVerdict = 'error';
        submitMessage = 'Submission timed out.';
      } else if (finalStatus === 'failed') {
        submitVerdict = 'error';
        submitMessage = outcome.capturedStderr.trim() || outcome.errorMessage || `Process exited with code ${outcome.exitCode}`;
      } else if (!expected) {
        submitVerdict = 'pending';
        submitMessage = 'No expected output configured for this language.';
      } else {
        const grade = gradeOutput(expected, outcome.capturedStdout);
        if (grade.passed) {
          submitVerdict = 'accepted';
          submitMessage = 'All outputs matched.';
          submitScore = 100;
        } else {
          submitVerdict = 'wrong_answer';
          submitMessage = grade.diff
            ? `Output did not match expected.\n\n${grade.diff}`
            : 'Output did not match expected.';
          submitScore = 0;
        }
      }
      registry.patchRecord(id, { submitVerdict, submitMessage, submitScore });
      await updateSession(id, { submitVerdict, submitMessage, submitScore }).catch(() => {});
    }

    await markFinal(
      id,
      finalStatus,
      outcome.exitCode,
      outcome.errorMessage ?? null,
      outcome.stdoutBytes,
      outcome.stderrBytes,
      now
    );
  };

  const { isQueued, removeIfQueued } = submitJob(mode, job);

  // Stash the queue handle on the entry so cancel can pop a queued job
  // without spawning anything.
  (entry as unknown as { removeIfQueued: () => boolean }).removeIfQueued = removeIfQueued;

  return { id, queued: isQueued() };
}

export async function listSessions(userId: string, opts?: { activeOnly?: boolean; limit?: number }): Promise<SessionRecord[]> {
  return listSessionRecords(userId, opts);
}

export async function getSession(userId: string, id: string): Promise<SessionRecord | null> {
  // Prefer the live entry's record so callers see fresh PID / byte counts
  // without waiting for the next DB flush.
  const live = registry.getEntry(id);
  if (live) return live.record.userId === userId ? live.record : null;
  return getSessionById(userId, id);
}

/**
 * Graceful cancel.
 *   - queued       → remove from queue, mark cancelled.
 *   - starting/running → abort signal fires → runtime tree-kills.
 *   - terminal     → no-op.
 */
export async function cancelSession(id: string): Promise<void> {
  const entry = registry.getEntry(id);
  if (!entry) return;
  if (isTerminal(entry.record.status)) return;

  const removeQueued = (entry as unknown as { removeIfQueued?: () => boolean }).removeIfQueued;
  if (removeQueued?.()) {
    await markCancelled(id, 'Cancelled while queued');
    return;
  }
  entry.abort.abort();
}

/**
 * Hard kill — same path as cancel for baremetal (treeKill is already
 * SIGKILL). For docker we'll issue `docker kill -s KILL` from the runtime
 * itself. The abort path covers both.
 */
export async function killSession(id: string): Promise<void> {
  // For now: same as cancel. The runtime's abort handler kills the whole
  // process tree / container. We keep a separate function for API symmetry
  // and to leave room for "skip the graceful stop" later.
  return cancelSession(id);
}

/**
 * Subscribe to a session's log stream. Returns the unsubscribe fn and the
 * record (so the consumer can decide whether the session is already done).
 */
export function subscribeToLogs(
  id: string,
  cb: (chunk: LogChunk) => void
): { unsubscribe: () => void; record: SessionRecord | null } {
  const entry = registry.getEntry(id);
  if (!entry) return { unsubscribe: () => {}, record: null };
  const unsubscribe = registry.subscribe(id, cb);
  return { unsubscribe, record: entry.record };
}

/**
 * Wait until a session reaches a terminal status, then return the final
 * record (re-fetched from the registry/DB). The legacy `/api/execute` shim
 * uses this to keep its old synchronous return shape.
 */
export async function awaitCompletion(id: string): Promise<SessionRecord | null> {
  const entry = registry.getEntry(id);
  if (entry) {
    await entry.done;
  }
  return entry ? getSession(entry.record.userId, id) : null;
}

export { queueSnapshot };

// ── Warm pool ─────────────────────────────────────────────────────────────

export interface PrewarmResult {
  /** True when a warm-up was scheduled (or a host is already ready). */
  warming: boolean;
  reason?: string;
}

/**
 * Ask the pool to prepare a warm Python host for a module. Safe to call on
 * every page open — it's idempotent per requirement set, and it no-ops for
 * modules light enough that a cold start is already fast.
 */
export function prewarmForProblem(problemId: string): PrewarmResult {
  const problem = resolveProblem(problemId);
  if (!problem) return { warming: false, reason: 'unknown problem' };
  if (problem.type !== 'coding') return { warming: false, reason: 'not a coding module' };
  if (!problem.languages.includes('python')) return { warming: false, reason: 'not a python module' };

  const spec = pool.specFor(problem.requirementsPath);
  if (!pool.isPoolable(spec)) return { warming: false, reason: 'nothing worth preloading' };

  pool.scheduleWarm(spec);
  return { warming: true };
}

export { poolSnapshot } from './runtime/pool.js';

// ── Internal status transitions ───────────────────────────────────────────

async function transition(id: string, status: SessionRecord['status']): Promise<void> {
  registry.patchRecord(id, { status });
  await updateSession(id, { status }).catch((err) => {
    console.warn('[sandbox] transition update failed', id, status, err);
  });
}

async function markCancelled(id: string, message: string): Promise<void> {
  const entry = registry.getEntry(id);
  const startedAt = entry?.record.startedAt ?? Date.now();
  await markFinal(id, 'cancelled', null, message, 0, message.length, startedAt);
  registry.publish(id, { kind: 'stderr', data: `${message}\n` });
}

async function markFinal(
  id: string,
  status: SessionRecord['status'],
  exitCode: number | null,
  errorMessage: string | null,
  stdoutBytes: number,
  stderrBytes: number,
  startedAt: number
): Promise<void> {
  const completedAt = Date.now();
  const durationMs = completedAt - startedAt;
  registry.patchRecord(id, {
    status, exitCode, errorMessage, stdoutBytes, stderrBytes, completedAt
  });
  await updateSession(id, {
    status, exitCode, errorMessage, stdoutBytes, stderrBytes, completedAt
  }).catch((err) => {
    console.warn('[sandbox] markFinal update failed', id, err);
  });
  registry.markDone(id, status, exitCode, durationMs);
}

// ── Buffered stdout/stderr for the /api/execute compat shim ──────────────

/**
 * Collect everything emitted for a session into a single { stdout, stderr }
 * pair. Subscribes immediately; resolves when the session reaches a
 * terminal status.
 */
export async function collectOutput(id: string): Promise<{
  stdout: string;
  stderr: string;
  status: SessionRecord['status'];
  exitCode: number | null;
  durationMs: number;
}> {
  const entry = registry.getEntry(id);
  let stdout = '';
  let stderr = '';
  let status: SessionRecord['status'] = 'queued';
  let exitCode: number | null = null;
  let durationMs = 0;
  const startedAt = entry?.record.startedAt ?? Date.now();

  if (entry) {
    const unsub = registry.subscribe(id, (chunk) => {
      if (chunk.kind === 'stdout') stdout += chunk.data;
      else if (chunk.kind === 'stderr') stderr += chunk.data;
      else if (chunk.kind === 'status') status = chunk.status;
      else if (chunk.kind === 'exit') {
        exitCode = chunk.exitCode;
        durationMs = chunk.durationMs;
      }
    });
    await entry.done;
    unsub();
  }

  const finalRecord = entry ? await getSession(entry.record.userId, id) : null;
  if (finalRecord) {
    status = finalRecord.status;
    exitCode = finalRecord.exitCode;
    if (durationMs === 0 && finalRecord.completedAt) {
      durationMs = finalRecord.completedAt - finalRecord.startedAt;
    }
  } else if (durationMs === 0) {
    durationMs = Date.now() - startedAt;
  }

  return { stdout, stderr, status, exitCode, durationMs };
}
