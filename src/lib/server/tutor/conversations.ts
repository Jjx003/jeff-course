/**
 * Persistence for tutor conversations, one thread per (user, module).
 *
 * SERVER-SIDE ONLY.
 */

import { randomUUID } from 'node:crypto';
import { dbAll, dbReady, dbRun } from '../db.js';
import type { TutorMessage, TutorRole, TutorToolStep } from '$lib/types/tutor.js';

/** How many prior turns are replayed to the model on each request. */
export const HISTORY_TURN_LIMIT = 20;

interface TutorMessageRow {
  id: string;
  role: string;
  content: string;
  created_at: number | bigint;
  steps: string | null;
}

/** Tool steps are stored as a JSON array; a malformed value is not fatal. */
function parseSteps(raw: string | null): TutorToolStep[] | undefined {
  if (!raw) return undefined;
  try {
    const parsed = JSON.parse(raw) as TutorToolStep[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : undefined;
  } catch {
    return undefined;
  }
}

function toMessage(row: TutorMessageRow): TutorMessage {
  const steps = parseSteps(row.steps);
  return {
    id: row.id,
    role: row.role === 'assistant' ? 'assistant' : 'user',
    content: row.content,
    createdAt: Number(row.created_at),
    ...(steps ? { steps } : {})
  };
}

export async function getConversation(
  userId: string,
  problemId: string,
  limit?: number
): Promise<TutorMessage[]> {
  await dbReady;
  const rows = await dbAll<TutorMessageRow>(
    `SELECT id, role, content, created_at, steps
       FROM tutor_messages
      WHERE user_id = ? AND problem_id = ?
      ORDER BY created_at ASC, id ASC`,
    [userId, problemId]
  );
  const messages = rows.map(toMessage);
  return limit && messages.length > limit ? messages.slice(-limit) : messages;
}

export async function appendMessage(
  userId: string,
  problemId: string,
  role: TutorRole,
  content: string,
  steps?: TutorToolStep[]
): Promise<TutorMessage> {
  await dbReady;
  const message: TutorMessage = {
    id: randomUUID(),
    role,
    content,
    createdAt: Date.now(),
    ...(steps && steps.length > 0 ? { steps } : {})
  };
  await dbRun(
    `INSERT INTO tutor_messages (id, user_id, problem_id, role, content, created_at, steps)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [
      message.id,
      userId,
      problemId,
      role,
      content,
      message.createdAt,
      message.steps ? JSON.stringify(message.steps) : null
    ]
  );
  return message;
}

export async function clearConversation(userId: string, problemId: string): Promise<void> {
  await dbReady;
  await dbRun('DELETE FROM tutor_messages WHERE user_id = ? AND problem_id = ?', [
    userId,
    problemId
  ]);
}
