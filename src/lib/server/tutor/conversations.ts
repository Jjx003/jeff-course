/**
 * Persistence for tutor conversations, one thread per (user, module).
 *
 * SERVER-SIDE ONLY.
 */

import { randomUUID } from 'node:crypto';
import { dbAll, dbReady, dbRun } from '../db.js';
import type { TutorMessage, TutorRole } from '$lib/types/tutor.js';

/** How many prior turns are replayed to the model on each request. */
export const HISTORY_TURN_LIMIT = 20;

interface TutorMessageRow {
  id: string;
  role: string;
  content: string;
  created_at: number | bigint;
}

function toMessage(row: TutorMessageRow): TutorMessage {
  return {
    id: row.id,
    role: row.role === 'assistant' ? 'assistant' : 'user',
    content: row.content,
    createdAt: Number(row.created_at)
  };
}

export async function getConversation(
  userId: string,
  problemId: string,
  limit?: number
): Promise<TutorMessage[]> {
  await dbReady;
  const rows = await dbAll<TutorMessageRow>(
    `SELECT id, role, content, created_at
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
  content: string
): Promise<TutorMessage> {
  await dbReady;
  const message: TutorMessage = {
    id: randomUUID(),
    role,
    content,
    createdAt: Date.now()
  };
  await dbRun(
    `INSERT INTO tutor_messages (id, user_id, problem_id, role, content, created_at)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [message.id, userId, problemId, role, content, message.createdAt]
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
