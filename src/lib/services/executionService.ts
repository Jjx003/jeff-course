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

export interface ExecutionService {
  /** Execute code and return stdout/stderr/status. */
  run(request: RunRequest): Promise<RunResult>;

  /** Submit code for grading and return a verdict. */
  submit(request: SubmitRequest): Promise<SubmitResult>;
}
