/**
 * Grader-message parsing.
 *
 * The sandbox stores a submission verdict as a single `submitMessage`
 * string, and for a wrong answer that string is a one-line headline
 * followed by the unified diff produced by `buildDiff` on the server:
 *
 *   Output did not match expected.
 *
 *   --- expected
 *   +++ actual
 *     Layer 0: 12.5
 *   - Layer 1: 24.0
 *   + Layer 1: 99.9
 *
 * Rendering that blob verbatim is what made the Submit panel unreadable.
 * This module splits it back into a headline plus structured rows so the
 * panel can show a real comparison, and reconstructs each side's full text
 * for the side-by-side view and the copy buttons.
 *
 * Pure + client-safe: no imports from $lib/server.
 */

import type { DiffRow } from '$lib/types/execution.js';

const DIFF_HEADER = '--- expected\n+++ actual\n';

export interface ParsedGraderMessage {
  /** Headline with the diff stripped out. Always non-empty. */
  summary: string;
  /** Structured rows, or null when the message carried no diff. */
  diff: DiffRow[] | null;
  expectedText: string;
  actualText: string;
}

/** Rows that represent an actual difference (i.e. everything but `same`). */
export function countMismatches(diff: DiffRow[]): number {
  return diff.filter((r) => r.kind !== 'same').length;
}

/** Index of the first differing row, or -1 when the sides agree. */
export function firstMismatchIndex(diff: DiffRow[]): number {
  return diff.findIndex((r) => r.kind !== 'same');
}

/**
 * Pair a run of expected-only lines with the run of actual-only lines that
 * immediately follows it. Overlapping positions become `changed` rows; the
 * leftovers on either side become `missing` / `extra`.
 */
function emitRun(rows: DiffRow[], minus: string[], plus: string[], expNo: number, actNo: number): [number, number] {
  const paired = Math.min(minus.length, plus.length);
  for (let i = 0; i < paired; i++) {
    rows.push({ kind: 'changed', expected: minus[i], actual: plus[i], expectedNo: expNo++, actualNo: actNo++ });
  }
  for (let i = paired; i < minus.length; i++) {
    rows.push({ kind: 'missing', expected: minus[i], expectedNo: expNo++ });
  }
  for (let i = paired; i < plus.length; i++) {
    rows.push({ kind: 'extra', actual: plus[i], actualNo: actNo++ });
  }
  return [expNo, actNo];
}

/**
 * Parse the raw diff body (everything after the `--- expected` header).
 */
function parseDiffBody(body: string): DiffRow[] {
  const rows: DiffRow[] = [];
  let minus: string[] = [];
  let plus: string[] = [];
  let expNo = 1;
  let actNo = 1;

  const flush = () => {
    if (!minus.length && !plus.length) return;
    [expNo, actNo] = emitRun(rows, minus, plus, expNo, actNo);
    minus = [];
    plus = [];
  };

  for (const raw of body.split('\n')) {
    if (raw.startsWith('- ')) {
      // A `-` after a `+` starts a fresh run — the previous pairing is done.
      if (plus.length) flush();
      minus.push(raw.slice(2));
    } else if (raw.startsWith('+ ')) {
      plus.push(raw.slice(2));
    } else {
      flush();
      const text = raw.startsWith('  ') ? raw.slice(2) : raw;
      rows.push({ kind: 'same', expected: text, actual: text, expectedNo: expNo++, actualNo: actNo++ });
    }
  }
  flush();
  return rows;
}

function reconstruct(rows: DiffRow[], side: 'expected' | 'actual'): string {
  return rows
    .filter((r) => r[side] !== undefined)
    .map((r) => r[side] as string)
    .join('\n');
}

export function parseGraderMessage(message: string): ParsedGraderMessage {
  const text = message ?? '';
  const headerAt = text.indexOf(DIFF_HEADER);

  if (headerAt === -1) {
    return { summary: text.trim(), diff: null, expectedText: '', actualText: '' };
  }

  const summary = text.slice(0, headerAt).trim() || 'Output did not match the expected result.';
  const body = text.slice(headerAt + DIFF_HEADER.length);
  const diff = parseDiffBody(body);

  return {
    summary,
    diff,
    expectedText: reconstruct(diff, 'expected'),
    actualText: reconstruct(diff, 'actual')
  };
}
