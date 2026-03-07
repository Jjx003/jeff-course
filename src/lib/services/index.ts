/**
 * Service registry / dependency injection entry point.
 *
 * All application code that needs a service should import from here,
 * never from a specific local/ implementation directly.
 *
 * EXTENSION POINT: to add a "remote" mode, check an environment variable
 * here and return the remote implementations instead of the local ones.
 * No other file needs to change.
 *
 * Example future pattern:
 *   const mode = import.meta.env.VITE_MODE ?? 'local';
 *   export const draftStorage = mode === 'remote'
 *     ? remoteDraftStorage
 *     : localDraftStorage;
 */

// Client-side persistence services (localStorage-backed)
export { localDraftStorage as draftStorage } from './local/draftStorage.local.js';
export { localRunHistoryStorage as runHistoryStorage } from './local/runHistoryStorage.local.js';
export { localSubmissionStorage as submissionStorage } from './local/submissionStorage.local.js';

// Execution service
export { localExecutionService as executionService } from './local/executionService.local.js';
export { generateId } from './local/executionService.local.js';

// NOTE: CourseRepository is NOT exported here because it is server-side only.
// Server load functions import localCourseRepository directly from
// services/local/courseRepository.local.ts.
