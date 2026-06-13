import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { createUser, listUsers } from '$lib/server/auth.js';

export const load: PageServerLoad = async ({ locals }) => {
  return {
    users: await listUsers(),
    currentUserId: locals.user?.id ?? null
  };
};

export const actions: Actions = {
  create: async ({ request }) => {
    const form = await request.formData();
    const name = String(form.get('name') ?? '');
    try {
      await createUser({ name, role: 'learner' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not create profile.';
      return fail(400, { name, error: message });
    }
    return { ok: true };
  }
};
