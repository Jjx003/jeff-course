/**
 * Types for the lightweight gamification layer.
 *
 * Design intent: surface progress and consistency without turning the course
 * into a slot machine. Everything here is descriptive — there are no
 * countdowns, leaderboards, or virtual currencies.
 */

import type { Difficulty, ModuleType } from './course.js';

/** Stable IDs for achievements. Kept narrow on purpose. */
export type AchievementId =
  | 'first-solve'
  | 'five-solves'
  | 'twenty-solves'
  | 'streak-3'
  | 'streak-7'
  | 'streak-30'
  | 'track-complete'
  | 'polyglot'
  | 'persistent'
  | 'theorist'
  | 'well-rounded';

export interface AchievementDef {
  id: AchievementId;
  title: string;
  description: string;
  /** Optional grouping for the UI. */
  category: 'milestone' | 'consistency' | 'depth';
}

export interface Achievement extends AchievementDef {
  /** Unix ms when this achievement was first unlocked, or null if locked. */
  unlockedAt: number | null;
  /** Progress toward the achievement, in [0, 1]. */
  progress: number;
  /** Human-readable progress label (e.g. "3 / 7 days"). */
  progressLabel: string;
}

/**
 * One row in the activity heatmap. `date` is an ISO date string (YYYY-MM-DD)
 * in the server's local timezone.
 */
export interface ActivityDay {
  date: string;
  /** Count of distinct contributions on this day (solves + readings). */
  count: number;
  /** Whether the user solved at least one problem (vs. only reading). */
  solved: boolean;
}

export interface TrackProgress {
  slug: string;
  title: string;
  total: number;
  completed: number;
  /** Whether this track has been fully completed. */
  done: boolean;
}

/** Personal-record style highlights, all derived (no separate table). */
export interface Highlights {
  longestStreak: number;
  mostActiveDayCount: number;
  mostActiveDate: string | null;
  firstActivityAt: number | null;
  totalActivityDays: number;
}

export interface StatsSummary {
  /** Current streak in days (using the server's local timezone, 1-day grace). */
  currentStreak: number;
  /** Whether today already counts toward the streak. */
  practicedToday: boolean;
  /** Total points earned (never decreases). */
  totalPoints: number;
  /** Total coding problems solved (unique). */
  problemsSolved: number;
  /** Total reading modules completed. */
  readingsCompleted: number;
  /** Total submission attempts (across all problems). */
  totalSubmissions: number;
  achievements: Achievement[];
  trackProgress: TrackProgress[];
  /** One year of activity, oldest first. */
  activity: ActivityDay[];
  highlights: Highlights;
}

/** Per-problem completion state used by track listings and the problem page. */
export interface ProblemCompletion {
  problemId: string;
  type: ModuleType;
  completed: boolean;
  /** Unix ms when completed, if known. */
  completedAt: number | null;
  /** For coding problems, how many points the first solve was worth. */
  points: number;
  difficulty: Difficulty;
}
