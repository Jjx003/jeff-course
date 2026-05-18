import type { PageServerLoad } from './$types';
import { getStatsSummary } from '$lib/server/stats';

export const load: PageServerLoad = async () => {
  const stats = await getStatsSummary();
  return { stats };
};
