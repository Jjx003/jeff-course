/**
 * Sandbox types — shared across runtime backends, queue, persistence, and
 * API routes.
 *
 * SERVER-SIDE ONLY.
 */

import type { Language } from '$lib/types/course.js';

/**
 * The execution backend used to run user code.
 *
 *   baremetal   — spawn directly on the host (current behaviour). No isolation,
 *                 no resource limits, full access to host GPU drivers.
 *   docker      — short-lived `docker run --rm` container with mem/cpu limits
 *                 and no network by default.
 *   docker-gpu  — same as docker but with `--gpus all` (NVIDIA Container Toolkit).
 */
export type SandboxMode = 'baremetal' | 'docker' | 'docker-gpu';

/**
 * Lifecycle state of a session.
 *
 *   queued    — accepted, waiting for a free slot.
 *   starting  — pulling/building image or warming up the process.
 *   running   — child process active and streaming output.
 *   completed — finished cleanly (exit code 0).
 *   cancelled — user pressed Cancel (graceful stop).
 *   killed    — user pressed Kill (SIGKILL / docker kill).
 *   failed    — non-zero exit code, compilation failure, etc.
 *   crashed   — server process died while this session was alive. Marked
 *               at boot time so we never leave "running" rows behind.
 */
export type SessionStatus =
  | 'queued'
  | 'starting'
  | 'running'
  | 'completed'
  | 'cancelled'
  | 'killed'
  | 'failed'
  | 'crashed';

/** Whether the user clicked Run or Submit. */
export type SessionAction = 'run' | 'submit';

/**
 * GPU passthrough request. `none` omits any docker `--gpus` flag; `all`
 * exposes every GPU; `{ device: N }` exposes only device N.
 */
export type GpuRequest = 'none' | 'all' | { device: number };

export interface ResourceLimits {
  /** RAM in megabytes. 0 = unlimited (baremetal only). */
  memoryMb: number;
  /** CPU shares as float. 0 = unlimited (baremetal only). */
  cpus: number;
  /** GPU passthrough — only meaningful for `docker-gpu`. */
  gpu: GpuRequest;
  /** Wall-clock timeout. */
  timeoutMs: number;
}

/**
 * A request to start a new session. Resources and mode may be omitted; the
 * server applies sensible defaults.
 */
export interface StartSessionRequest {
  userId: string;
  problemId: string;                  // "{trackSlug}/{problemSlug}"
  language: Language;
  code: string;
  action: SessionAction;
  mode?: SandboxMode;                 // defaults to 'baremetal'
  resources?: Partial<ResourceLimits>;
}

/**
 * The full server-side picture of a session at any moment. Stored in DuckDB
 * and surfaced via the API.
 *
 * `exit_code === null` means the process either hasn't finished yet or was
 * killed before it could report one.
 */
export interface SessionRecord {
  id: string;
  userId: string;
  problemId: string;
  language: Language;
  action: SessionAction;
  mode: SandboxMode;
  status: SessionStatus;
  /** Docker container name; null for baremetal. */
  containerName: string | null;
  /** Host PID of the immediate child; useful for diagnostics. */
  hostPid: number | null;
  startedAt: number;
  completedAt: number | null;
  exitCode: number | null;
  errorMessage: string | null;
  resources: ResourceLimits;
  stdoutBytes: number;
  stderrBytes: number;
  /** Grading verdict for `action: 'submit'` sessions, populated on exit. */
  submitVerdict?: 'accepted' | 'wrong_answer' | 'error' | 'pending' | null;
  /** Human-readable message accompanying the verdict. */
  submitMessage?: string | null;
  /** Score 0-100 (null for pending / non-graded). */
  submitScore?: number | null;
}

/**
 * One frame from a session's live output stream. Emitted via SSE so the UI
 * can render incrementally.
 */
export type LogChunk =
  | { kind: 'stdout'; data: string }
  | { kind: 'stderr'; data: string }
  | { kind: 'status'; status: SessionStatus; message?: string }
  | { kind: 'exit'; exitCode: number | null; durationMs: number };

/**
 * One row in the `sandbox_preferences` table. Persists the user's last-used
 * run mode + resource limits per track so the picker remembers their pick.
 */
export interface TrackPreference {
  userId: string;
  trackSlug: string;
  preferredMode: SandboxMode;
  resources: ResourceLimits;
}

/**
 * Result of probing the host for Docker / GPU support. Cached at boot.
 */
export interface SandboxCapabilities {
  docker: {
    available: boolean;
    version?: string;
    /** Hint surfaced in the UI when docker is missing. */
    reason?: string;
  };
  gpu: {
    available: boolean;
    deviceCount?: number;
    reason?: string;
  };
}

// ── Defaults ─────────────────────────────────────────────────────────────

export const DEFAULT_RESOURCES_BAREMETAL: ResourceLimits = {
  memoryMb: 0,
  cpus: 0,
  gpu: 'none',
  timeoutMs: 60_000
};

export const DEFAULT_RESOURCES_DOCKER: ResourceLimits = {
  memoryMb: 4096,
  cpus: 2,
  gpu: 'none',
  timeoutMs: 600_000
};

export const DEFAULT_RESOURCES_DOCKER_GPU: ResourceLimits = {
  memoryMb: 16_384,
  cpus: 4,
  gpu: 'all',
  timeoutMs: 1_200_000
};

export function defaultResourcesFor(mode: SandboxMode): ResourceLimits {
  if (mode === 'docker') return { ...DEFAULT_RESOURCES_DOCKER };
  if (mode === 'docker-gpu') return { ...DEFAULT_RESOURCES_DOCKER_GPU };
  return { ...DEFAULT_RESOURCES_BAREMETAL };
}

/**
 * Terminal statuses — once a session reaches one of these, it is immutable.
 * Used both by the registry (to clean up) and the UI (to hide cancel/kill).
 */
export const TERMINAL_STATUSES: readonly SessionStatus[] = [
  'completed',
  'cancelled',
  'killed',
  'failed',
  'crashed'
];

export function isTerminal(status: SessionStatus): boolean {
  return TERMINAL_STATUSES.includes(status);
}
