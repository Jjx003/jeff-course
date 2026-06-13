import { json, redirect, type Handle } from '@sveltejs/kit';
import { getUserFromCookies, hasAnyUsers } from '$lib/server/auth.js';

const PUBLIC_PATHS = ['/auth/setup', '/auth/sign-in', '/auth/sign-out'];
const PUBLIC_FILES = ['/favicon.png'];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_FILES.includes(pathname) || PUBLIC_PATHS.includes(pathname);
}

export const handle: Handle = async ({ event, resolve }) => {
  const hasUsers = await hasAnyUsers();
  const user = hasUsers ? await getUserFromCookies(event.cookies) : null;
  event.locals.hasUsers = hasUsers;
  event.locals.user = user;

  const pathname = event.url.pathname;
  if (!hasUsers && pathname !== '/auth/setup' && !isPublicPath(pathname)) {
    throw redirect(303, '/auth/setup');
  }
  if (hasUsers && !user && !isPublicPath(pathname)) {
    if (pathname.startsWith('/api/')) {
      return json({ error: 'Authentication required' }, { status: 401 });
    }
    throw redirect(303, `/auth/sign-in?next=${encodeURIComponent(pathname)}`);
  }
  if (user && pathname === '/auth/setup') {
    throw redirect(303, '/tracks');
  }

  return resolve(event);
};
