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

// Persistence services — DuckDB-backed via API routes
export { apiDraftStorage as draftStorage } from './api/draftStorage.api.js';
export { apiRunHistoryStorage as runHistoryStorage } from './api/runHistoryStorage.api.js';
export { apiSubmissionStorage as submissionStorage } from './api/submissionStorage.api.js';

// Gamification services
export { apiStatsService as statsService } from './api/statsService.api.js';
export { apiReadingProgressService as readingProgressService } from './api/readingProgressService.api.js';
export { apiStudyTimeService as studyTimeService } from './api/studyTimeService.api.js';

// Execution service
export { localExecutionService as executionService } from './local/executionService.local.js';
export { generateId } from './local/executionService.local.js';

// NOTE: CourseRepository is NOT exported here because it is server-side only.
// Server load functions import localCourseRepository directly from
// services/local/courseRepository.local.ts.
