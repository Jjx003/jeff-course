/**
 * Persistence for `flashcards` modules.
 *
 * SERVER-SIDE ONLY. The scheduling maths lives in
 * `$lib/flashcards/scheduler.ts` so the browser can preview intervals on the
 * grade buttons; this module is only about reading and writing the state.
 *
 * A deck counts as complete once every card has been graded `good` or `easy`
 * at least once. That is deliberately a "you have been through the whole deck"
 * bar rather than a mastery bar: mastery is what the recurring due queue on
 * /review is for, and locking module completion behind a never-ending review
 * schedule would make the track impossible to finish.
 */

import { randomUUID } from 'node:crypto';
import { dbAll, dbRun, dbReady } from './db.js';
import { freshState, isFlashcardGrade, scheduleNext } from '$lib/flashcards/scheduler.js';
import type {
  FlashcardCardState,
  FlashcardGrade,
  FlashcardProgress
} from '$lib/types/course.js';

export { isFlashcardGrade };

interface StateRow {
  problem_id: string;
  card_id: string;
  reps: number;
  lapses: number;
  ease: number;
  interval_days: number;
  due_at: number;
  last_grade: string | null;
  last_reviewed_at: number | null;
  learned: boolean;
}

const STATE_COLUMNS = `problem_id, card_id, reps, lapses, ease, interval_days, due_at,
                       last_grade, last_reviewed_at, learned`;

function rowToState(row: StateRow): FlashcardCardState {
  return {
    cardId: row.card_id,
    reps: Number(row.reps),
    lapses: Number(row.lapses),
    ease: Number(row.ease),
    intervalDays: Number(row.interval_days),
    dueAt: Number(row.due_at),
    lastGrade: isFlashcardGrade(row.last_grade) ? row.last_grade : null,
    lastReviewedAt: row.last_reviewed_at === null ? null : Number(row.last_reviewed_at),
    learned: Boolean(row.learned)
  };
}

async function loadStates(userId: string, problemId: string): Promise<Map<string, FlashcardCardState>> {
  const rows = await dbAll<StateRow>(
    `SELECT ${STATE_COLUMNS} FROM flashcard_states WHERE user_id = ? AND problem_id = ?`,
    [userId, problemId]
  );
  return new Map(rows.map((row) => [row.card_id, rowToState(row)]));
}

/**
 * Aggregate deck progress. `cardIds` comes from `cards.yaml`, so cards that
 * were edited out of a deck after a learner reviewed them drop out of the
 * counts instead of inflating them.
 */
export async function getDeckProgress(
  userId: string,
  problemId: string,
  cardIds: string[],
  now: number = Date.now()
): Promise<FlashcardProgress> {
  await dbReady;
  const stateMap = await loadStates(userId, problemId);
  const states: FlashcardCardState[] = cardIds.map((id) => stateMap.get(id) ?? freshState(id));

  let seen = 0;
  let learned = 0;
  let due = 0;
  let fresh = 0;
  let nextDueAt: number | null = null;

  for (const state of states) {
    if (state.lastReviewedAt === null) {
      fresh += 1;
      continue;
    }
    seen += 1;
    if (state.learned) learned += 1;
    if (state.dueAt <= now) due += 1;
    else if (nextDueAt === null || state.dueAt < nextDueAt) nextDueAt = state.dueAt;
  }

  const reviewRows = await dbAll<{ n: number }>(
    'SELECT COUNT(*) AS n FROM flashcard_reviews WHERE user_id = ? AND problem_id = ?',
    [userId, problemId]
  );

  const completionRows = await dbAll<{ completed_at: number }>(
    'SELECT completed_at FROM reading_completions WHERE user_id = ? AND problem_id = ?',
    [userId, problemId]
  );
  const passedAt = completionRows.length > 0 ? Number(completionRows[0].completed_at) : null;

  return {
    problemId,
    totalCards: cardIds.length,
    seen,
    learned,
    due,
    fresh,
    reviews: Number(reviewRows[0]?.n ?? 0),
    nextDueAt,
    hasPassed: passedAt !== null,
    passedAt,
    states
  };
}

/**
 * Serializes work per deck. `recordFlashcardReview` reads the card's state,
 * computes the next one, and writes it back; without this, two reviews of the
 * same card that overlap both read the same prior state and the second write
 * silently discards the first. The client deliberately does not await each
 * review before advancing, so overlap is the normal case, not a rare one.
 *
 * A per-deck chain rather than a global lock: different decks never touch the
 * same rows, and DuckDB is a single writer anyway, so this only has to stop
 * one deck's own reviews from interleaving.
 */
const deckWriteChains = new Map<string, Promise<unknown>>();

function withDeckLock<T>(key: string, work: () => Promise<T>): Promise<T> {
  const previous = deckWriteChains.get(key) ?? Promise.resolve();
  // Swallow the predecessor's rejection so one failed review does not poison
  // every later review of the same deck.
  const result = previous.then(work, work);
  deckWriteChains.set(
    key,
    result.catch(() => undefined).finally(() => {
      if (deckWriteChains.get(key) === chained) deckWriteChains.delete(key);
    })
  );
  const chained = deckWriteChains.get(key)!;
  return result;
}

export interface FlashcardReviewOutcome {
  state: FlashcardCardState;
  progress: FlashcardProgress;
  /** True when this review was the one that finished the deck's first pass. */
  wasNewCompletion: boolean;
}

/**
 * Record one graded review and reschedule the card. `cardIds` is the full
 * authored deck, used to decide whether this review completed the first pass.
 */
export function recordFlashcardReview(args: {
  userId: string;
  problemId: string;
  cardId: string;
  grade: FlashcardGrade;
  responseMs: number;
  cardIds: string[];
}): Promise<FlashcardReviewOutcome> {
  return withDeckLock(`${args.userId}/${args.problemId}`, () => recordReviewLocked(args));
}

async function recordReviewLocked(args: {
  userId: string;
  problemId: string;
  cardId: string;
  grade: FlashcardGrade;
  responseMs: number;
  cardIds: string[];
}): Promise<FlashcardReviewOutcome> {
  await dbReady;
  const now = Date.now();
  // Clamp to 10 minutes: a card left open over lunch should not poison the
  // response-time stats.
  const responseMs = Math.max(0, Math.min(10 * 60 * 1000, Math.floor(args.responseMs)));

  const stateMap = await loadStates(args.userId, args.problemId);
  const prev = stateMap.get(args.cardId) ?? freshState(args.cardId);
  const next = scheduleNext(prev, args.grade, now);

  await dbRun(
    `INSERT INTO flashcard_states
       (user_id, problem_id, card_id, reps, lapses, ease, interval_days, due_at,
        last_grade, last_reviewed_at, learned)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT (user_id, problem_id, card_id) DO UPDATE SET
       reps = EXCLUDED.reps,
       lapses = EXCLUDED.lapses,
       ease = EXCLUDED.ease,
       interval_days = EXCLUDED.interval_days,
       due_at = EXCLUDED.due_at,
       last_grade = EXCLUDED.last_grade,
       last_reviewed_at = EXCLUDED.last_reviewed_at,
       learned = EXCLUDED.learned`,
    [
      args.userId,
      args.problemId,
      args.cardId,
      next.reps,
      next.lapses,
      next.ease,
      next.intervalDays,
      Math.round(next.dueAt),
      next.lastGrade,
      Math.round(next.lastReviewedAt ?? now),
      next.learned
    ]
  );

  await dbRun(
    `INSERT INTO flashcard_reviews (id, user_id, problem_id, card_id, grade, response_ms, reviewed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [randomUUID(), args.userId, args.problemId, args.cardId, args.grade, responseMs, now]
  );

  const progress = await getDeckProgress(args.userId, args.problemId, args.cardIds, now);

  let wasNewCompletion = false;
  const firstPassDone = args.cardIds.length > 0 && progress.learned >= args.cardIds.length;
  if (firstPassDone && !progress.hasPassed) {
    await dbRun(
      `INSERT INTO reading_completions (user_id, problem_id, completed_at) VALUES (?, ?, ?)
       ON CONFLICT (user_id, problem_id) DO NOTHING`,
      [args.userId, args.problemId, now]
    );
    // Only claim the completion if this call is the one that inserted it, so
    // the reward toast fires exactly once.
    const inserted = await dbAll<{ completed_at: number }>(
      'SELECT completed_at FROM reading_completions WHERE user_id = ? AND problem_id = ?',
      [args.userId, args.problemId]
    );
    const completedAt = inserted.length > 0 ? Number(inserted[0].completed_at) : now;
    wasNewCompletion = completedAt === now;
    progress.hasPassed = true;
    progress.passedAt = completedAt;
  }

  return { state: next, progress, wasNewCompletion };
}

/**
 * Wipe a learner's scheduling state for one deck so they can start over. The
 * review log and the module's completion record are left alone: they did do
 * the work, and losing the completion because they wanted a clean re-run
 * would be a bad trade.
 */
export async function resetDeck(userId: string, problemId: string): Promise<void> {
  await dbReady;
  await dbRun('DELETE FROM flashcard_states WHERE user_id = ? AND problem_id = ?', [
    userId,
    problemId
  ]);
}

/** Every stored card state for a learner, keyed by problem id then card id. */
export async function loadAllStates(
  userId: string
): Promise<Map<string, Map<string, FlashcardCardState>>> {
  await dbReady;
  const rows = await dbAll<StateRow>(
    `SELECT ${STATE_COLUMNS} FROM flashcard_states WHERE user_id = ?`,
    [userId]
  );
  const byProblem = new Map<string, Map<string, FlashcardCardState>>();
  for (const row of rows) {
    let inner = byProblem.get(row.problem_id);
    if (!inner) {
      inner = new Map();
      byProblem.set(row.problem_id, inner);
    }
    inner.set(row.card_id, rowToState(row));
  }
  return byProblem;
}

/**
 * Due/fresh/learned counts for a set of decks, for the cross-course /review
 * page. One query, then bucketed in memory — deck sizes are small and this
 * keeps the counts honest about cards edited out of a deck after review.
 */
export async function getDueByDeck(
  userId: string,
  decks: { problemId: string; cardIds: string[] }[],
  now: number = Date.now()
): Promise<Map<string, { due: number; fresh: number; learned: number }>> {
  const out = new Map<string, { due: number; fresh: number; learned: number }>();
  if (decks.length === 0) return out;
  const byProblem = await loadAllStates(userId);

  for (const deck of decks) {
    const inner = byProblem.get(deck.problemId);
    let due = 0;
    let fresh = 0;
    let learned = 0;
    for (const cardId of deck.cardIds) {
      const state = inner?.get(cardId);
      if (!state || state.lastReviewedAt === null) {
        fresh += 1;
        continue;
      }
      if (state.learned) learned += 1;
      if (state.dueAt <= now) due += 1;
    }
    out.set(deck.problemId, { due, fresh, learned });
  }

  return out;
}
