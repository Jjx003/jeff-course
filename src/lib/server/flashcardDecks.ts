/**
 * Cross-course deck discovery.
 *
 * SERVER-SIDE ONLY.
 *
 * The /review page and its API route both need "every flashcards module in
 * every track this learner is enrolled in, with its cards and its due counts".
 * That crosses three concerns — course content, enrollment, and scheduling —
 * so it lives here instead of in `flashcards.ts` (pure scheduling) or in a
 * route (not reusable).
 */

import { loadAllTracks, loadProblem } from '$lib/content/courseLoader.js';
import { getEnrolledTrackSlugs } from './enrollments.js';
import { getDueByDeck } from './flashcards.js';
import type { Flashcard, FlashcardDueDeck } from '$lib/types/course.js';

export interface LoadedDeck {
  problemId: string;
  trackSlug: string;
  trackTitle: string;
  problemSlug: string;
  problemTitle: string;
  deckTitle: string;
  cards: Flashcard[];
}

/**
 * Every flashcards module the learner is enrolled in, in track order.
 * Decks with no cards are skipped so an unfinished module never shows up as
 * a zero-card review target.
 */
export function loadEnrolledDecks(enrolled: Set<string>): LoadedDeck[] {
  const out: LoadedDeck[] = [];
  for (const track of loadAllTracks()) {
    if (!enrolled.has(track.slug)) continue;
    for (const meta of track.problems) {
      if (meta.type !== 'flashcards') continue;
      const problem = loadProblem(track.slug, meta.slug);
      const cards = problem?.deck?.cards ?? [];
      if (cards.length === 0) continue;
      out.push({
        problemId: `${track.slug}/${meta.slug}`,
        trackSlug: track.slug,
        trackTitle: track.title,
        problemSlug: meta.slug,
        problemTitle: meta.title,
        deckTitle: problem?.deck?.title ?? meta.title,
        cards
      });
    }
  }
  return out;
}

/** Due/fresh/learned counts per deck, ready for the review dashboard. */
export async function summarizeDueDecks(
  userId: string,
  now: number = Date.now()
): Promise<{ decks: LoadedDeck[]; summary: FlashcardDueDeck[] }> {
  const enrolled = await getEnrolledTrackSlugs(userId);
  const decks = loadEnrolledDecks(enrolled);
  const counts = await getDueByDeck(
    userId,
    decks.map((deck) => ({ problemId: deck.problemId, cardIds: deck.cards.map((c) => c.id) })),
    now
  );

  const summary: FlashcardDueDeck[] = decks.map((deck) => {
    const count = counts.get(deck.problemId) ?? { due: 0, fresh: deck.cards.length, learned: 0 };
    return {
      trackSlug: deck.trackSlug,
      trackTitle: deck.trackTitle,
      problemSlug: deck.problemSlug,
      problemTitle: deck.problemTitle,
      deckTitle: deck.deckTitle,
      totalCards: deck.cards.length,
      due: count.due,
      fresh: count.fresh,
      learned: count.learned
    };
  });

  return { decks, summary };
}
