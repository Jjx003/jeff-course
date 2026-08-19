import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { summarizeDueDecks } from '$lib/server/flashcardDecks';

export const GET: RequestHandler = async ({ locals }) => {
  const { summary } = await summarizeDueDecks(locals.user!.id);
  return json(summary);
};
