import type { PageServerLoad } from './$types';
import { getStatsSummary } from '$lib/server/stats';

export const load: PageServerLoad = async ({ locals }) => {
  const stats = await getStatsSummary(locals.user!.id);
  return { stats };
};
