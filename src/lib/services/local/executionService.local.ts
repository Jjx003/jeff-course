/**
 * ApiExecutionService
 *
 * Real execution service that delegates to the server-side `/api/execute`
 * route, which in turn uses `executor.ts` (child_process.spawn + UV/g++).
 *
 * Previously this was a browser-only mock that parsed print()/cout statements.
 * That mock has been replaced entirely: all execution now happens on the server.
 *
 * The interface contract (RunRequest → RunResult, SubmitRequest → SubmitResult)
 * is unchanged, so no call sites in the UI need updating.
 *
 * CLIENT-SIDE ONLY — uses fetch(), no Node.js APIs.
 */

import type { ExecutionService } from '../executionService.js';
import type { RunRequest, RunResult, SubmitRequest, SubmitResult } from '$lib/types/execution.js';

// ── Helpers ───────────────────────────────────────────────────────────────

/** Generate a unique run/submission ID (used by +page.svelte via services/index.ts). */
function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

// ── Implementation ────────────────────────────────────────────────────────

class ApiExecutionService implements ExecutionService {
  async run(request: RunRequest): Promise<RunResult> {
    const [trackSlug, problemSlug] = request.problemId.split('/');

    const response = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'run',
        language: request.language,
        code: request.code,
        problemId: `${trackSlug}/${problemSlug}`
      })
    });

    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText);
      return {
        stdout: '',
        stderr: `Execution request failed (${response.status}): ${text}`,
        durationMs: null,
        success: false,
        status: 'error'
      };
    }

    const result: RunResult = await response.json();
    return result;
  }

  async submit(request: SubmitRequest): Promise<SubmitResult> {
    const [trackSlug, problemSlug] = request.problemId.split('/');

    const response = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'submit',
        language: request.language,
        code: request.code,
        problemId: `${trackSlug}/${problemSlug}`
      })
    });

    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText);
      return {
        verdict: 'error',
        message: `Submission request failed (${response.status}): ${text}`,
        score: null
      };
    }

    const result: SubmitResult = await response.json();
    return result;
  }
}

export const localExecutionService = new ApiExecutionService();

// Re-export generateId — imported by services/index.ts and used in +page.svelte
export { generateId };
