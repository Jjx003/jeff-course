import { randomUUID } from 'node:crypto';
import type { Cookies } from '@sveltejs/kit';
import { dbAll, dbReady, dbRun } from './db.js';

const SESSION_COOKIE = 'jeff_course_session';
const SESSION_TTL_MS = 1000 * 60 * 60 * 24 * 30;
const FIRST_USER_ID = 'local';

export type AuthUser = NonNullable<App.Locals['user']>;

interface UserRow {
  id: string;
  name: string;
  role: 'admin' | 'learner';
}

function normalizeName(name: string): string {
  return name.trim().replace(/\s+/g, ' ');
}

function cookieOptions(expires: Date) {
  return {
    path: '/',
    httpOnly: true,
    sameSite: 'lax' as const,
    secure: false,
    expires
  };
}

export async function hasAnyUsers(): Promise<boolean> {
  await dbReady;
  const rows = await dbAll<{ count: number }>('SELECT COUNT(*) AS count FROM users');
  return Number(rows[0]?.count ?? 0) > 0;
}

export async function listUsers(): Promise<AuthUser[]> {
  await dbReady;
  const rows = await dbAll<UserRow>(
    'SELECT id, name, role FROM users ORDER BY created_at ASC'
  );
  return rows.map((row) => ({ id: row.id, name: row.name, role: row.role }));
}

export async function createUser(args: {
  name: string;
  role?: 'admin' | 'learner';
  useFirstUserId?: boolean;
}): Promise<AuthUser> {
  await dbReady;
  const name = normalizeName(args.name);
  if (name.length < 2 || name.length > 40) {
    throw new Error('Name must be 2-40 characters.');
  }
  const id = args.useFirstUserId ? FIRST_USER_ID : randomUUID();
  const now = Date.now();
  await dbRun(
    `INSERT INTO users (id, name, role, password_hash, created_at, last_login_at)
     VALUES (?, ?, ?, ?, ?, NULL)`,
    [id, name, args.role ?? 'learner', 'passwordless', now]
  );
  return { id, name, role: args.role ?? 'learner' };
}

export async function getUserById(id: string): Promise<AuthUser | null> {
  await dbReady;
  const rows = await dbAll<UserRow>(
    'SELECT id, name, role FROM users WHERE id = ? LIMIT 1',
    [id]
  );
  const row = rows[0];
  if (!row) return null;
  await dbRun('UPDATE users SET last_login_at = ? WHERE id = ?', [Date.now(), row.id]);
  return { id: row.id, name: row.name, role: row.role };
}

export async function createSession(cookies: Cookies, userId: string): Promise<void> {
  await dbReady;
  const currentId = cookies.get(SESSION_COOKIE);
  if (currentId) await dbRun('DELETE FROM auth_sessions WHERE id = ?', [currentId]);
  const id = randomUUID();
  const now = Date.now();
  const expiresAt = now + SESSION_TTL_MS;
  await dbRun(
    'INSERT INTO auth_sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)',
    [id, userId, now, expiresAt]
  );
  cookies.set(SESSION_COOKIE, id, cookieOptions(new Date(expiresAt)));
}

export async function destroySession(cookies: Cookies): Promise<void> {
  await dbReady;
  const id = cookies.get(SESSION_COOKIE);
  if (id) {
    await dbRun('DELETE FROM auth_sessions WHERE id = ?', [id]);
  }
  cookies.delete(SESSION_COOKIE, { path: '/' });
}

export async function getUserFromCookies(cookies: Cookies): Promise<AuthUser | null> {
  await dbReady;
  const id = cookies.get(SESSION_COOKIE);
  if (!id) return null;
  const now = Date.now();
  const rows = await dbAll<UserRow>(
    `SELECT u.id, u.name, u.role
       FROM auth_sessions s
       JOIN users u ON u.id = s.user_id
      WHERE s.id = ? AND s.expires_at > ?
      LIMIT 1`,
    [id, now]
  );
  if (rows.length === 0) {
    cookies.delete(SESSION_COOKIE, { path: '/' });
    return null;
  }
  return { id: rows[0].id, name: rows[0].name, role: rows[0].role };
}
