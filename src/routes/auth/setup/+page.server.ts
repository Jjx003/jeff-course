import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { createSession, createUser } from '$lib/server/auth.js';

export const load: PageServerLoad = async ({ locals }) => {
  if (locals.hasUsers) throw redirect(303, '/auth/sign-in');
  return {};
};

export const actions: Actions = {
  default: async ({ cookies, request }) => {
    const form = await request.formData();
    const name = String(form.get('name') ?? '');

    try {
      const user = await createUser({
        name,
        role: 'admin',
        useFirstUserId: true
      });
      await createSession(cookies, user.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not create the first profile.';
      return fail(400, { name, error: message });
    }

    throw redirect(303, '/tracks');
  }
};
