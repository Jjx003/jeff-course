/**
 * Pure spaced-repetition scheduling. No database, no fetch — safe to import
 * from both the server and the browser, which is why the module page can show
 * "Good → 6d" on the buttons without a round trip.
 *
 * The algorithm is a trimmed SM-2. Each card carries an ease factor, an
 * interval in days, and a due timestamp. A review applies one of four grades:
 *
 *   again → back into learning, due in ~10 minutes, ease drops, lapse counted
 *   hard  → short interval, ease drops slightly
 *   good  → 1 day on the first pass, then interval * ease each time
 *   easy  → the good interval stretched by a bonus, ease rises
 */

import type { Flashcard, FlashcardCardState, FlashcardGrade } from '$lib/types/course.js';

const MINUTE_MS = 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;

export const MIN_EASE = 1.3;
export const MAX_EASE = 2.8;
export const START_EASE = 2.5;
/** Cards never get scheduled further out than this. */
export const MAX_INTERVAL_DAYS = 365;
/** How soon a lapsed card comes back inside the same sitting. */
export const RELEARN_MINUTES = 10;

export const FLASHCARD_GRADES: readonly FlashcardGrade[] = ['again', 'hard', 'good', 'easy'];

export function isFlashcardGrade(value: unknown): value is FlashcardGrade {
  return typeof value === 'string' && (FLASHCARD_GRADES as readonly string[]).includes(value);
}

/** The state of a card this learner has never reviewed. */
export function freshState(cardId: string): FlashcardCardState {
  return {
    cardId,
    reps: 0,
    lapses: 0,
    ease: START_EASE,
    intervalDays: 0,
    dueAt: 0,
    lastGrade: null,
    lastReviewedAt: null,
    learned: false
  };
}

function clampEase(ease: number): number {
  return Math.min(MAX_EASE, Math.max(MIN_EASE, ease));
}

/** Apply one grade to a card and return its next scheduling state. */
export function scheduleNext(
  prev: FlashcardCardState,
  grade: FlashcardGrade,
  now: number
): FlashcardCardState {
  let { reps, lapses, ease, intervalDays } = prev;
  let learned = prev.learned;
  let dueAt: number;

  if (grade === 'again') {
    if (prev.learned) lapses += 1;
    reps = 0;
    ease = clampEase(ease - 0.2);
    intervalDays = 0;
    dueAt = now + RELEARN_MINUTES * MINUTE_MS;
  } else if (grade === 'hard') {
    ease = clampEase(ease - 0.15);
    // A hard card still in learning stays short; a mature one creeps forward
    // instead of jumping by the full ease factor.
    intervalDays = intervalDays === 0 ? 1 : Math.max(1, intervalDays * 1.2);
    reps += 1;
    dueAt = now + intervalDays * DAY_MS;
  } else {
    // good / easy — both count as recall, so the card becomes "learned".
    if (grade === 'easy') ease = clampEase(ease + 0.15);
    if (intervalDays === 0) {
      // A card is only ever at interval 0 when it is new or has just lapsed,
      // and both of those also reset reps, so there is no third case here.
      intervalDays = grade === 'easy' ? 4 : 1;
    } else {
      intervalDays = intervalDays * ease * (grade === 'easy' ? 1.3 : 1);
    }
    reps += 1;
    learned = true;
    dueAt = now + intervalDays * DAY_MS;
  }

  intervalDays = Math.min(MAX_INTERVAL_DAYS, intervalDays);
  if (intervalDays > 0) dueAt = now + intervalDays * DAY_MS;

  return {
    cardId: prev.cardId,
    reps,
    lapses,
    ease,
    intervalDays,
    dueAt,
    lastGrade: grade,
    lastReviewedAt: now,
    learned
  };
}

/** Short label for what each button would do, e.g. `{ good: "6d" }`. */
export function gradePreview(
  state: FlashcardCardState,
  now: number = Date.now()
): Record<FlashcardGrade, string> {
  const out = {} as Record<FlashcardGrade, string>;
  for (const grade of FLASHCARD_GRADES) {
    const days = scheduleNext(state, grade, now).intervalDays;
    // One decimal below 10 days, so adjacent buttons never collapse to the
    // same label (2.5d and 3.4d both round to "3d" otherwise).
    out[grade] =
      days === 0
        ? `${RELEARN_MINUTES}m`
        : days < 10
          ? `${(Math.round(days * 10) / 10).toString().replace(/\.0$/, '')}d`
          : `${Math.round(days)}d`;
  }
  return out;
}

/**
 * Build a review queue: cards that have fallen due first (oldest due date
 * first, because those are the most nearly forgotten), then never-seen cards
 * up to `newPerSession`, then the whole thing capped at `maxPerSession`.
 *
 * With `includeAll`, ordering and caps are ignored and the full deck is
 * returned — that is the "cram the whole deck" mode a learner wants the night
 * before an interview, when the spacing schedule is beside the point.
 */
export function buildQueue(
  cards: Flashcard[],
  states: FlashcardCardState[],
  opts: { newPerSession?: number; maxPerSession?: number; includeAll?: boolean } = {},
  now: number = Date.now()
): Flashcard[] {
  const stateMap = new Map(states.map((s) => [s.cardId, s]));
  const newPerSession = opts.newPerSession ?? 15;
  const maxPerSession = opts.maxPerSession ?? 60;

  if (opts.includeAll) return [...cards];

  const dueCards = cards
    .filter((card) => {
      const state = stateMap.get(card.id);
      return !!state && state.lastReviewedAt !== null && state.dueAt <= now;
    })
    .sort((a, b) => stateMap.get(a.id)!.dueAt - stateMap.get(b.id)!.dueAt);

  const freshCards = cards.filter((card) => {
    const state = stateMap.get(card.id);
    return !state || state.lastReviewedAt === null;
  });

  return [...dueCards, ...freshCards.slice(0, newPerSession)].slice(0, maxPerSession);
}

/** "in 3 days" / "in 4 hours" / "now", for due-date copy. */
export function formatDueIn(dueAt: number | null, now: number = Date.now()): string {
  if (dueAt === null) return '-';
  const ms = dueAt - now;
  if (ms <= 0) return 'now';
  const minutes = Math.max(1, Math.round(ms / MINUTE_MS));
  if (minutes < 60) return `in ${minutes} min`;
  const hours = ms / (60 * 60 * 1000);
  if (hours < 36) return `in ${Math.round(hours)} h`;
  return `in ${Math.floor(hours / 24)} d`;
}
