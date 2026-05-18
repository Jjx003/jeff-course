/**
 * ReadingProgressService interface.
 *
 * Reading modules don't produce code submissions, so we track their
 * completion explicitly. One row per `problemId`; the first mark-complete is
 * the canonical completion timestamp.
 */

export interface ReadingProgressService {
  isCompleted(problemId: string): Promise<boolean>;
  /** Returns whether this was the first time the user marked it complete. */
  markComplete(problemId: string): Promise<{ wasNew: boolean }>;
}
