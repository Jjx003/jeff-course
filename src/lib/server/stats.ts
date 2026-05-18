/**
 * Server-side gamification engine.
 *
 * Pure functions over the existing `submissions` table + the new
 * `reading_completions` and `achievements` tables, plus the static course
 * content loaded via `loadAllTracks`.
 *
 * SERVER-SIDE ONLY. Never import from a component or client-side file.
 *
 * Design intent
 *   - Streaks use the server's local date (good enough for a single-user
 *     local app) with a 1-day grace: today OR yesterday counts as "alive".
 *   - Points are awarded for the *first* accepted submission of a problem
 *     and for the first completion of a reading module. Grinding does not
 *     pay.
 *   - Achievements are persisted on first unlock so the UI can show a
 *     stable "earned on" date.
 */

import { dbReady, dbAll, dbRun } from './db.js';
import { getTotalActiveMs, getActiveMsForDateKey } from './studyTime.js';
import { loadAllTracks } from '$lib/content/courseLoader.js';
import type { Difficulty, ModuleType, Track } from '$lib/types/course.js';
import type {
  Achievement,
  AchievementDef,
  AchievementId,
  ActivityDay,
  Highlights,
  ProblemCompletion,
  StatsSummary,
  TrackProgress
} from '$lib/types/gamification.js';

// ── Scoring ──────────────────────────────────────────────────────────────

const DIFFICULTY_POINTS: Record<Difficulty, number> = {
  beginner: 10,
  intermediate: 20,
  advanced: 35
};
const READING_POINTS = 5;

function pointsForCoding(difficulty: Difficulty): number {
  return DIFFICULTY_POINTS[difficulty] ?? 10;
}

// ── Achievement definitions ──────────────────────────────────────────────

export const ACHIEVEMENT_DEFS: AchievementDef[] = [
  { id: 'first-solve',    title: 'First Steps',     description: 'Solve your first coding problem.',          category: 'milestone'   },
  { id: 'five-solves',    title: 'Getting Going',   description: 'Solve 5 coding problems.',                  category: 'milestone'   },
  { id: 'twenty-solves',  title: 'Practiced',       description: 'Solve 20 coding problems.',                 category: 'milestone'   },
  { id: 'streak-3',       title: 'Consistent',      description: 'Practice 3 days in a row.',                 category: 'consistency' },
  { id: 'streak-7',       title: 'Dedicated',       description: 'Practice 7 days in a row.',                 category: 'consistency' },
  { id: 'streak-30',      title: 'Habit Formed',    description: 'Practice 30 days in a row.',                category: 'consistency' },
  { id: 'track-complete', title: 'Track Conqueror', description: 'Complete every problem in a track.',        category: 'milestone'   },
  { id: 'polyglot',       title: 'Polyglot',        description: 'Solve a problem in both Python and C++.',   category: 'depth'       },
  { id: 'persistent',     title: 'Persistent',      description: 'Solve a problem after 3+ submission tries.', category: 'depth'      },
  { id: 'theorist',       title: 'Theorist',        description: 'Complete 5 reading modules.',               category: 'depth'       },
  { id: 'well-rounded',   title: 'Well-Rounded',    description: 'Be active across 3 different tracks.',      category: 'depth'       },
  { id: 'hours-1',        title: 'Warm-up',         description: 'Spend 1 hour learning.',                    category: 'time'        },
  { id: 'hours-10',       title: 'Focused Time',    description: 'Spend 10 hours learning.',                  category: 'time'        },
  { id: 'hours-50',       title: 'Deep Practice',   description: 'Spend 50 hours learning.',                  category: 'time'        },
  { id: 'hours-100',      title: 'Centurion',       description: 'Spend 100 hours learning.',                 category: 'time'        }
];

// ── Date helpers (local timezone) ────────────────────────────────────────

/** YYYY-MM-DD in the server's local timezone for the given epoch ms. */
export function toLocalDateKey(epochMs: number): string {
  const d = new Date(epochMs);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Epoch ms for local midnight of the date `daysAgo` days ago (0 = today). */
function localMidnightDaysAgo(daysAgo: number): number {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - daysAgo);
  return d.getTime();
}

function dateKeyDaysAgo(daysAgo: number): string {
  return toLocalDateKey(localMidnightDaysAgo(daysAgo));
}

// ── DB row shapes ────────────────────────────────────────────────────────

type SubmissionRow = {
  problem_id: string;
  language: string;
  result: string;
  timestamp: number;
};
type ReadingRow = { problem_id: string; completed_at: number };
type AchievementRow = { id: string; unlocked_at: number };

// ── Aggregated view of raw activity ──────────────────────────────────────

interface ActivityFacts {
  /** First-accepted timestamp keyed by problemId (independent of language). */
  firstSolveAt: Map<string, number>;
  /** Set of languages a problem was solved in (for Polyglot). */
  solveLanguages: Map<string, Set<string>>;
  /** Total submission attempts per problemId. */
  submissionCount: Map<string, number>;
  /** Submission attempts up to (and including) the first accepted submission. */
  attemptsToSolve: Map<string, number>;
  /** First-completion timestamp keyed by problemId for reading modules. */
  readingCompletedAt: Map<string, number>;
  /** Total submissions across everything (for the dashboard). */
  totalSubmissions: number;
}

async function loadActivityFacts(): Promise<ActivityFacts> {
  await dbReady;

  const subs = await dbAll<SubmissionRow>(
    'SELECT problem_id, language, result, timestamp FROM submissions ORDER BY timestamp ASC',
    []
  );
  const reads = await dbAll<ReadingRow>(
    'SELECT problem_id, completed_at FROM reading_completions',
    []
  );

  const firstSolveAt = new Map<string, number>();
  const solveLanguages = new Map<string, Set<string>>();
  const submissionCount = new Map<string, number>();
  const attemptsToSolve = new Map<string, number>();
  const attemptsSeen = new Map<string, number>(); // running counter pre-solve

  for (const row of subs) {
    const pid = row.problem_id;
    submissionCount.set(pid, (submissionCount.get(pid) ?? 0) + 1);

    let verdict = '';
    try {
      verdict = (JSON.parse(row.result) as { verdict?: string }).verdict ?? '';
    } catch {
      verdict = '';
    }

    if (!firstSolveAt.has(pid)) {
      attemptsSeen.set(pid, (attemptsSeen.get(pid) ?? 0) + 1);
    }

    if (verdict === 'accepted') {
      if (!firstSolveAt.has(pid)) {
        firstSolveAt.set(pid, Number(row.timestamp));
        attemptsToSolve.set(pid, attemptsSeen.get(pid) ?? 1);
      }
      let langs = solveLanguages.get(pid);
      if (!langs) {
        langs = new Set();
        solveLanguages.set(pid, langs);
      }
      langs.add(row.language);
    }
  }

  const readingCompletedAt = new Map<string, number>();
  for (const r of reads) {
    readingCompletedAt.set(r.problem_id, Number(r.completed_at));
  }

  return {
    firstSolveAt,
    solveLanguages,
    submissionCount,
    attemptsToSolve,
    readingCompletedAt,
    totalSubmissions: subs.length
  };
}

// ── Streak ───────────────────────────────────────────────────────────────

/**
 * Compute the current streak using local dates.
 *
 * Rules:
 *   - An "active day" is any date with at least one solve or reading completion.
 *   - The streak counts back from today (or from yesterday if today is empty,
 *     a one-day grace so missing today doesn't immediately destroy the chain).
 *   - The streak ends at the first gap.
 */
function computeStreaks(activityDates: Set<string>): {
  current: number;
  longest: number;
  practicedToday: boolean;
} {
  const today = dateKeyDaysAgo(0);
  const yesterday = dateKeyDaysAgo(1);
  const practicedToday = activityDates.has(today);

  // Start at today if active, else yesterday if active, else streak is 0.
  let start = -1;
  if (practicedToday) start = 0;
  else if (activityDates.has(yesterday)) start = 1;

  let current = 0;
  if (start >= 0) {
    let i = start;
    while (activityDates.has(dateKeyDaysAgo(i))) {
      current++;
      i++;
    }
  }

  // Longest streak: scan all active dates.
  let longest = 0;
  if (activityDates.size > 0) {
    const sorted = [...activityDates].sort();
    let run = 1;
    longest = 1;
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i - 1] + 'T00:00:00');
      const curr = new Date(sorted[i] + 'T00:00:00');
      const diffDays = Math.round((curr.getTime() - prev.getTime()) / (24 * 60 * 60 * 1000));
      if (diffDays === 1) {
        run++;
        longest = Math.max(longest, run);
      } else {
        run = 1;
      }
    }
  }

  return { current, longest, practicedToday };
}

// ── Heatmap (last 52 weeks aligned to weeks) ─────────────────────────────

const HEATMAP_DAYS = 52 * 7;

function buildActivityHeatmap(
  solveDates: Map<string, number>,
  readingDates: Map<string, number>
): ActivityDay[] {
  const days: ActivityDay[] = [];
  for (let i = HEATMAP_DAYS - 1; i >= 0; i--) {
    const date = dateKeyDaysAgo(i);
    const solves = solveDates.get(date) ?? 0;
    const readings = readingDates.get(date) ?? 0;
    days.push({
      date,
      count: solves + readings,
      solved: solves > 0
    });
  }
  return days;
}

// ── Achievement evaluation ───────────────────────────────────────────────

interface AchievementContext {
  facts: ActivityFacts;
  tracks: Track[];
  currentStreak: number;
  longestStreak: number;
  problemsSolved: number;
  readingsCompleted: number;
  /** Total active study time in ms (orphan-filtered). */
  totalActiveMs: number;
}

interface AchievementEval {
  unlocked: boolean;
  progress: number;
  progressLabel: string;
}

function evalAchievement(id: AchievementId, ctx: AchievementContext): AchievementEval {
  switch (id) {
    case 'first-solve':
      return ratio(ctx.problemsSolved, 1, `${Math.min(ctx.problemsSolved, 1)} / 1 solved`);
    case 'five-solves':
      return ratio(ctx.problemsSolved, 5, `${Math.min(ctx.problemsSolved, 5)} / 5 solved`);
    case 'twenty-solves':
      return ratio(ctx.problemsSolved, 20, `${Math.min(ctx.problemsSolved, 20)} / 20 solved`);
    case 'streak-3':
      return ratio(ctx.longestStreak, 3, `${Math.min(ctx.longestStreak, 3)} / 3 days`);
    case 'streak-7':
      return ratio(ctx.longestStreak, 7, `${Math.min(ctx.longestStreak, 7)} / 7 days`);
    case 'streak-30':
      return ratio(ctx.longestStreak, 30, `${Math.min(ctx.longestStreak, 30)} / 30 days`);
    case 'track-complete': {
      // Best per-track progress across all tracks.
      let best = 0;
      let bestTitle = '—';
      let bestCount = 0;
      let bestTotal = 0;
      for (const t of ctx.tracks) {
        const codingProblems = t.problems.filter((p) => p.type === 'coding');
        const readings = t.problems.filter((p) => p.type === 'reading');
        const total = codingProblems.length + readings.length;
        if (total === 0) continue;
        const solved =
          codingProblems.filter((p) =>
            ctx.facts.firstSolveAt.has(`${t.slug}/${p.slug}`)
          ).length +
          readings.filter((p) =>
            ctx.facts.readingCompletedAt.has(`${t.slug}/${p.slug}`)
          ).length;
        const r = total === 0 ? 0 : solved / total;
        if (r > best) {
          best = r;
          bestTitle = t.title;
          bestCount = solved;
          bestTotal = total;
        }
      }
      return {
        unlocked: best >= 1,
        progress: Math.min(best, 1),
        progressLabel: bestTotal > 0 ? `${bestCount} / ${bestTotal} · ${bestTitle}` : 'no tracks yet'
      };
    }
    case 'polyglot': {
      let unlocked = false;
      for (const langs of ctx.facts.solveLanguages.values()) {
        if (langs.has('python') && langs.has('cpp')) {
          unlocked = true;
          break;
        }
      }
      return {
        unlocked,
        progress: unlocked ? 1 : 0,
        progressLabel: unlocked ? 'Done' : 'Solve one problem in both languages'
      };
    }
    case 'persistent': {
      let best = 0;
      for (const n of ctx.facts.attemptsToSolve.values()) {
        if (n > best) best = n;
      }
      return {
        unlocked: best >= 3,
        progress: Math.min(best / 3, 1),
        progressLabel: best >= 3 ? `${best} attempts` : `best run: ${best} / 3 attempts`
      };
    }
    case 'theorist':
      return ratio(ctx.readingsCompleted, 5, `${Math.min(ctx.readingsCompleted, 5)} / 5 readings`);
    case 'well-rounded': {
      // Distinct tracks with at least one activity.
      const tracksTouched = new Set<string>();
      for (const pid of ctx.facts.firstSolveAt.keys()) {
        tracksTouched.add(pid.split('/')[0]);
      }
      for (const pid of ctx.facts.readingCompletedAt.keys()) {
        tracksTouched.add(pid.split('/')[0]);
      }
      const n = tracksTouched.size;
      return ratio(n, 3, `${Math.min(n, 3)} / 3 tracks`);
    }
    case 'hours-1':
      return hoursRatio(ctx.totalActiveMs, 1);
    case 'hours-10':
      return hoursRatio(ctx.totalActiveMs, 10);
    case 'hours-50':
      return hoursRatio(ctx.totalActiveMs, 50);
    case 'hours-100':
      return hoursRatio(ctx.totalActiveMs, 100);
  }
}

/**
 * Hours-based ratio used by the time-based achievements. Renders e.g.
 * "12.3 / 50 hours" with a tenth precision so progress feels live without
 * being noisy.
 */
function hoursRatio(activeMs: number, targetHours: number): AchievementEval {
  const hours = activeMs / 3_600_000;
  const shown = Math.min(hours, targetHours);
  const label = `${shown.toFixed(1)} / ${targetHours} hours`;
  return {
    unlocked: hours >= targetHours,
    progress: targetHours === 0 ? 1 : Math.min(hours / targetHours, 1),
    progressLabel: label
  };
}

function ratio(current: number, target: number, label: string): AchievementEval {
  const p = target === 0 ? 1 : Math.min(current / target, 1);
  return { unlocked: current >= target, progress: p, progressLabel: label };
}

async function loadUnlockedAchievements(): Promise<Map<string, number>> {
  const rows = await dbAll<AchievementRow>('SELECT id, unlocked_at FROM achievements', []);
  return new Map(rows.map((r) => [r.id, Number(r.unlocked_at)]));
}

async function persistNewAchievements(ids: AchievementId[]): Promise<void> {
  if (ids.length === 0) return;
  const now = Date.now();
  for (const id of ids) {
    await dbRun(
      `INSERT INTO achievements (id, unlocked_at) VALUES (?, ?)
       ON CONFLICT (id) DO NOTHING`,
      [id, now]
    );
  }
}

// ── Track progress ───────────────────────────────────────────────────────

function computeTrackProgress(tracks: Track[], facts: ActivityFacts): TrackProgress[] {
  return tracks.map((t) => {
    const total = t.problems.length;
    let completed = 0;
    for (const p of t.problems) {
      const pid = `${t.slug}/${p.slug}`;
      const isDone =
        p.type === 'reading'
          ? facts.readingCompletedAt.has(pid)
          : facts.firstSolveAt.has(pid);
      if (isDone) completed++;
    }
    return {
      slug: t.slug,
      title: t.title,
      total,
      completed,
      done: total > 0 && completed === total
    };
  });
}

// ── Points ───────────────────────────────────────────────────────────────

function computePoints(tracks: Track[], facts: ActivityFacts): number {
  let total = 0;
  for (const t of tracks) {
    for (const p of t.problems) {
      const pid = `${t.slug}/${p.slug}`;
      if (p.type === 'coding' && facts.firstSolveAt.has(pid)) {
        total += pointsForCoding(p.difficulty);
      } else if (p.type === 'reading' && facts.readingCompletedAt.has(pid)) {
        total += READING_POINTS;
      }
    }
  }
  return total;
}

// ── Public API ───────────────────────────────────────────────────────────

/** One unified payload for the /stats page and the header badge. */
export async function getStatsSummary(): Promise<StatsSummary> {
  await dbReady;
  const facts = await loadActivityFacts();
  const tracks = await loadAllTracks();

  // Build the set of known problem IDs so we can filter activity to events
  // that actually correspond to current course content (orphan-safe).
  const knownProblemIds = new Set<string>();
  for (const t of tracks) {
    for (const p of t.problems) knownProblemIds.add(`${t.slug}/${p.slug}`);
  }

  // Bucket activity by day for the heatmap and the streak calculation.
  const solvesByDate = new Map<string, number>();
  for (const [pid, ts] of facts.firstSolveAt.entries()) {
    if (!knownProblemIds.has(pid)) continue;
    const key = toLocalDateKey(ts);
    solvesByDate.set(key, (solvesByDate.get(key) ?? 0) + 1);
  }
  const readingsByDate = new Map<string, number>();
  for (const [pid, ts] of facts.readingCompletedAt.entries()) {
    if (!knownProblemIds.has(pid)) continue;
    const key = toLocalDateKey(ts);
    readingsByDate.set(key, (readingsByDate.get(key) ?? 0) + 1);
  }

  const activeDateSet = new Set<string>([
    ...solvesByDate.keys(),
    ...readingsByDate.keys()
  ]);
  const streak = computeStreaks(activeDateSet);
  const heatmap = buildActivityHeatmap(solvesByDate, readingsByDate);

  // Highlights — most active day
  let mostActiveDayCount = 0;
  let mostActiveDate: string | null = null;
  for (const day of heatmap) {
    if (day.count > mostActiveDayCount) {
      mostActiveDayCount = day.count;
      mostActiveDate = day.date;
    }
  }
  const allTimestamps: number[] = [];
  for (const [pid, ts] of facts.firstSolveAt.entries()) {
    if (knownProblemIds.has(pid)) allTimestamps.push(ts);
  }
  for (const [pid, ts] of facts.readingCompletedAt.entries()) {
    if (knownProblemIds.has(pid)) allTimestamps.push(ts);
  }
  const firstActivityAt = allTimestamps.length === 0 ? null : Math.min(...allTimestamps);

  const trackProgress = computeTrackProgress(tracks, facts);

  // Only count completions that map to an actual course module. This makes
  // the dashboard robust against orphaned rows left behind by content
  // renames or stray API hits.
  let problemsSolved = 0;
  let readingsCompleted = 0;
  for (const t of tracks) {
    for (const p of t.problems) {
      const pid = `${t.slug}/${p.slug}`;
      if (p.type === 'coding' && facts.firstSolveAt.has(pid)) problemsSolved++;
      else if (p.type === 'reading' && facts.readingCompletedAt.has(pid)) readingsCompleted++;
    }
  }
  const totalPoints = computePoints(tracks, facts);

  // Study time — totals + today's bucket. Orphan-filtered against current
  // course content inside the helpers, so renamed problems don't inflate
  // numbers.
  const todayKey = dateKeyDaysAgo(0);
  const [totalActiveMs, activeMsToday] = await Promise.all([
    getTotalActiveMs(),
    getActiveMsForDateKey(todayKey)
  ]);

  // Achievements — evaluate, persist new unlocks, then return enriched list.
  const persisted = await loadUnlockedAchievements();
  const ctx: AchievementContext = {
    facts,
    tracks,
    currentStreak: streak.current,
    longestStreak: streak.longest,
    problemsSolved,
    readingsCompleted,
    totalActiveMs
  };

  const newlyUnlocked: AchievementId[] = [];
  const achievements: Achievement[] = ACHIEVEMENT_DEFS.map((def) => {
    const ev = evalAchievement(def.id, ctx);
    let unlockedAt = persisted.get(def.id) ?? null;
    if (ev.unlocked && unlockedAt === null) {
      newlyUnlocked.push(def.id);
    }
    return {
      ...def,
      progress: ev.progress,
      progressLabel: ev.progressLabel,
      unlockedAt
    };
  });
  if (newlyUnlocked.length > 0) {
    await persistNewAchievements(newlyUnlocked);
    const now = Date.now();
    for (const a of achievements) {
      if (newlyUnlocked.includes(a.id) && a.unlockedAt === null) {
        a.unlockedAt = now;
      }
    }
  }

  const highlights: Highlights = {
    longestStreak: streak.longest,
    mostActiveDayCount,
    mostActiveDate,
    firstActivityAt,
    totalActivityDays: activeDateSet.size
  };

  return {
    currentStreak: streak.current,
    practicedToday: streak.practicedToday,
    totalPoints,
    problemsSolved,
    readingsCompleted,
    totalSubmissions: facts.totalSubmissions,
    totalActiveMs,
    activeMsToday,
    achievements,
    trackProgress,
    activity: heatmap,
    highlights
  };
}

// ── Per-problem completion (used by track listings) ──────────────────────

export async function getCompletionsForTrack(
  trackSlug: string
): Promise<ProblemCompletion[]> {
  await dbReady;
  const facts = await loadActivityFacts();
  const tracks = await loadAllTracks();
  const track = tracks.find((t) => t.slug === trackSlug);
  if (!track) return [];
  return track.problems.map((p) => {
    const pid = `${trackSlug}/${p.slug}`;
    const isCoding = p.type === 'coding';
    const completedAt = isCoding
      ? facts.firstSolveAt.get(pid) ?? null
      : facts.readingCompletedAt.get(pid) ?? null;
    return {
      problemId: pid,
      type: p.type as ModuleType,
      completed: completedAt !== null,
      completedAt,
      points: isCoding ? pointsForCoding(p.difficulty) : READING_POINTS,
      difficulty: p.difficulty
    };
  });
}

/** Is a single problem completed? Used by the problem page for the toast. */
export async function isProblemCompleted(problemId: string): Promise<boolean> {
  await dbReady;
  const facts = await loadActivityFacts();
  return facts.firstSolveAt.has(problemId) || facts.readingCompletedAt.has(problemId);
}

/** Mark a reading module as complete. Idempotent. */
export async function markReadingCompleted(problemId: string): Promise<{ wasNew: boolean }> {
  await dbReady;
  const existing = await dbAll<{ problem_id: string }>(
    'SELECT problem_id FROM reading_completions WHERE problem_id = ?',
    [problemId]
  );
  if (existing.length > 0) return { wasNew: false };
  await dbRun(
    'INSERT INTO reading_completions (problem_id, completed_at) VALUES (?, ?)',
    [problemId, Date.now()]
  );
  return { wasNew: true };
}

/** Has a reading module been completed? */
export async function isReadingCompleted(problemId: string): Promise<boolean> {
  await dbReady;
  const rows = await dbAll<{ problem_id: string }>(
    'SELECT problem_id FROM reading_completions WHERE problem_id = ?',
    [problemId]
  );
  return rows.length > 0;
}
