/**
 * Client-safe types mirroring the server-side sandbox API.
 *
 * The full server-side types live in `src/lib/server/sandbox/types.ts`; that
 * module imports server-only deps (DuckDB, child_process) and must not be
 * pulled into the client bundle. This file is a pure data-shape mirror
 * intended for use in components and client services.
 */

import type { Language } from './course.js';

export type SandboxMode = 'baremetal' | 'docker' | 'docker-gpu';

export type SessionStatus =
  | 'queued'
  | 'starting'
  | 'running'
  | 'completed'
  | 'cancelled'
  | 'killed'
  | 'failed'
  | 'crashed';

export type SessionAction = 'run' | 'submit';

export type GpuRequest = 'none' | 'all' | { device: number };

export interface ResourceLimits {
  memoryMb: number;
  cpus: number;
  gpu: GpuRequest;
  timeoutMs: number;
}

export interface SessionRecord {
  id: string;
  problemId: string;
  language: Language;
  action: SessionAction;
  mode: SandboxMode;
  status: SessionStatus;
  containerName: string | null;
  hostPid: number | null;
  startedAt: number;
  completedAt: number | null;
  exitCode: number | null;
  errorMessage: string | null;
  resources: ResourceLimits;
  stdoutBytes: number;
  stderrBytes: number;
  submitVerdict?: 'accepted' | 'wrong_answer' | 'error' | 'pending' | null;
  submitMessage?: string | null;
  submitScore?: number | null;
}

export interface TrackPreference {
  trackSlug: string;
  preferredMode: SandboxMode;
  resources: ResourceLimits;
}

export interface SandboxCapabilities {
  docker: { available: boolean; version?: string; reason?: string };
  gpu: { available: boolean; deviceCount?: number; reason?: string };
}

export type LogChunk =
  | { kind: 'stdout'; data: string }
  | { kind: 'stderr'; data: string }
  | { kind: 'status'; status: SessionStatus; message?: string }
  | { kind: 'exit'; exitCode: number | null; durationMs: number };

export interface StartSessionRequest {
  problemId: string;
  language: Language;
  code: string;
  action: SessionAction;
  mode?: SandboxMode;
  resources?: Partial<ResourceLimits>;
}

export const TERMINAL_STATUSES: readonly SessionStatus[] = [
  'completed',
  'cancelled',
  'killed',
  'failed',
  'crashed'
];

export function isTerminalStatus(s: SessionStatus): boolean {
  return TERMINAL_STATUSES.includes(s);
}
