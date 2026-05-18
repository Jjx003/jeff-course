/**
 * ExecutionService interface.
 *
 * Abstracts code execution. The local implementation is a mock that returns
 * simulated output. A future remote implementation would call a sandboxed
 * execution API (e.g. a Docker-based runner, Judge0, or a custom backend).
 *
 * EXTENSION POINT: swap LocalExecutionService for RemoteExecutionService
 * without changing any call sites.
 */

import type { RunRequest, RunResult, SubmitRequest, SubmitResult } from '$lib/types/execution.js';

export interface ExecutionOptions {
  /**
   * When this aborts, the in-flight fetch is cancelled, which closes the
   * HTTP connection to /api/execute. The server observes the disconnect
   * via `request.signal` and tree-kills the spawned child process.
   */
  signal?: AbortSignal;
}

export interface ExecutionService {
  /** Execute code and return stdout/stderr/status. */
  run(request: RunRequest, opts?: ExecutionOptions): Promise<RunResult>;

  /** Submit code for grading and return a verdict. */
  submit(request: SubmitRequest, opts?: ExecutionOptions): Promise<SubmitResult>;
}
