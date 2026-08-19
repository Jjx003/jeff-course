import type { PageServerLoad } from './$types';
import { summarizeDueDecks } from '$lib/server/flashcardDecks';
import { loadAllStates } from '$lib/server/flashcards';
import type { Flashcard, FlashcardCardState } from '$lib/types/course.js';

/**
 * How many never-seen cards one sitting introduces, and the ceiling on a
 * single queue. Both live here rather than on the client so the page ships
 * only what a session can actually use.
 */
// Not exported: +page.server.ts only permits load/actions/config exports.
const NEW_CARD_ALLOWANCE = 20;
const MAX_SESSION_CARDS = 120;

export interface ReviewQueueItem {
  card: Flashcard;
  problemId: string;
  trackSlug: string;
  problemSlug: string;
  deckTitle: string;
  state: FlashcardCardState | null;
}

/**
 * The cross-course review queue.
 *
 * Everything the session needs is shipped in the initial load — card content,
 * per-card state, and deck labels — so flipping through cards never blocks on
 * a fetch. Grading still posts one review at a time to the owning deck's API
 * route, which keeps a single source of truth for scheduling.
 */
export const load: PageServerLoad = async ({ locals }) => {
  const now = Date.now();
  const [{ decks, summary }, statesByProblem] = await Promise.all([
    summarizeDueDecks(locals.user!.id, now),
    loadAllStates(locals.user!.id)
  ]);

  const due: ReviewQueueItem[] = [];
  const fresh: ReviewQueueItem[] = [];

  for (const deck of decks) {
    const states = statesByProblem.get(deck.problemId);
    for (const card of deck.cards) {
      const state = states?.get(card.id) ?? null;
      const item: ReviewQueueItem = {
        card,
        problemId: deck.problemId,
        trackSlug: deck.trackSlug,
        problemSlug: deck.problemSlug,
        deckTitle: deck.deckTitle,
        state
      };
      if (!state || state.lastReviewedAt === null) fresh.push(item);
      else if (state.dueAt <= now) due.push(item);
    }
  }

  // Most-overdue first: those are the cards closest to being forgotten.
  due.sort((a, b) => (a.state?.dueAt ?? 0) - (b.state?.dueAt ?? 0));

  // Counts come from the summary, so the queues can be trimmed to what a
  // sitting will consume without the dashboard numbers going wrong.
  const dueTotal = due.length;
  const freshTotal = fresh.length;

  return {
    summary,
    due: due.slice(0, MAX_SESSION_CARDS),
    fresh: fresh.slice(0, NEW_CARD_ALLOWANCE),
    dueTotal,
    freshTotal,
    newCardAllowance: NEW_CARD_ALLOWANCE,
    loadedAt: now
  };
};
