import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { createSession, getUserById, listUsers } from '$lib/server/auth.js';

export const load: PageServerLoad = async ({ locals, url }) => {
  if (!locals.hasUsers) throw redirect(303, '/auth/setup');
  return {
    next: url.searchParams.get('next') ?? '/tracks',
    users: await listUsers(),
    currentUserId: locals.user?.id ?? null
  };
};

export const actions: Actions = {
  default: async ({ cookies, request, url }) => {
    const form = await request.formData();
    const userId = String(form.get('userId') ?? '');
    const next = url.searchParams.get('next') ?? '/tracks';
    const user = await getUserById(userId);
    if (!user) {
      return fail(400, { error: 'That profile is no longer available.' });
    }
    await createSession(cookies, user.id);
    throw redirect(303, next.startsWith('/') ? next : '/tracks');
  }
};
