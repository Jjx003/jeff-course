/**
 * Tools the tutor can call to inspect what the learner is actually working
 * with.
 *
 * SERVER-SIDE ONLY.
 *
 * Everything here reads from the filesystem or DuckDB using the *server's*
 * idea of who the learner is and which module they are on. The browser never
 * supplies this material, so it cannot be used to talk the tutor into a
 * different learner's code or a module the learner is not enrolled in.
 *
 * This replaces the old approach of pasting the editor buffer into every
 * request's system prompt: the editor already autosaves to `drafts`, so the
 * code is fetched on demand and only when the tutor actually needs it.
 */

import { dbAll, dbReady } from '../db.js';
import type { Problem, Track } from '$lib/types/course.js';
import type { RunResult, SubmitResult } from '$lib/types/execution.js';

/** Keep any single tool result from crowding out the conversation. */
const RESULT_CHAR_LIMIT = 7000;
const STREAM_CHAR_LIMIT = 2500;

export interface ToolContext {
  userId: string;
  /** `${trackSlug}/${problemSlug}` */
  problemId: string;
  track: Track;
  problem: Problem;
  allowSolutions: boolean;
  /** Language the learner currently has selected in the editor. */
  language?: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  /** Short present-tense phrase shown in the UI while the tool runs. */
  label: (args: Record<string, unknown>, ctx: ToolContext) => string;
  run: (args: Record<string, unknown>, ctx: ToolContext) => Promise<string>;
}

// ── helpers ──────────────────────────────────────────────────────────────

function clip(text: string, limit = RESULT_CHAR_LIMIT): string {
  return text.length <= limit ? text : `${text.slice(0, limit)}\n[...truncated for length...]`;
}

/**
 * Line-number the code so the tutor can say "line 12" and mean it.
 */
function withLineNumbers(code: string): string {
  const lines = code.split('\n');
  const width = String(lines.length).length;
  return lines.map((line, i) => `${String(i + 1).padStart(width, ' ')} | ${line}`).join('\n');
}

/** Resolve the language argument against what the module actually supports. */
function resolveLanguage(args: Record<string, unknown>, ctx: ToolContext): string {
  const requested = typeof args.language === 'string' ? args.language : undefined;
  const supported = ctx.problem.languages ?? [];
  if (requested && supported.includes(requested as never)) return requested;
  if (ctx.language && supported.includes(ctx.language as never)) return ctx.language;
  return ctx.problem.defaultLanguage ?? supported[0] ?? 'python';
}

function parseJson<T>(raw: unknown): T | null {
  if (typeof raw !== 'string') return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function describeStream(name: string, text: string): string {
  const trimmed = (text ?? '').trim();
  if (!trimmed) return `${name}: (empty)`;
  return `${name}:\n${clip(trimmed, STREAM_CHAR_LIMIT)}`;
}

const LANGUAGE_PARAM = {
  type: 'string',
  enum: ['python', 'cpp'],
  description: 'Which language to look at. Defaults to the one the learner has open.'
};

// ── read_learner_code ────────────────────────────────────────────────────

const readLearnerCode: ToolDefinition = {
  name: 'read_learner_code',
  description:
    'Read the code the learner currently has in their editor for this module. ' +
    'Returns the code with line numbers. Call this before commenting on their ' +
    'implementation, and again after they say they changed something.',
  parameters: {
    type: 'object',
    properties: { language: LANGUAGE_PARAM },
    required: []
  },
  label: () => 'Reading your code',
  run: async (args, ctx) => {
    if (ctx.problem.type !== 'coding') {
      return 'This is not a coding module, so the learner has no editor buffer.';
    }
    const language = resolveLanguage(args, ctx);
    await dbReady;
    const rows = await dbAll<{ code: string; last_saved_at: number | bigint }>(
      `SELECT code, last_saved_at
         FROM drafts
        WHERE user_id = ? AND problem_id = ? AND language = ?`,
      [ctx.userId, ctx.problemId, language]
    );

    const starter = ctx.problem.starterCode?.[language as 'python' | 'cpp'] ?? '';
    const draft = rows[0]?.code;
    const code = draft ?? starter;

    if (!code.trim()) {
      return `The learner has not written any ${language} code yet, and this module ships no starter file.`;
    }

    const header = draft
      ? `The learner's current ${language} editor buffer`
      : `The learner has not edited anything yet. This is the unmodified ${language} starter file`;
    const unchanged =
      draft && starter.trim() && draft.trim() === starter.trim()
        ? '\n\nNote: this is byte-identical to the starter file — they have not begun.'
        : '';

    return clip(`${header}:\n\n${withLineNumbers(code)}${unchanged}`);
  }
};

// ── read_module_section ──────────────────────────────────────────────────

const readModuleSection: ToolDefinition = {
  name: 'read_module_section',
  description:
    'Read one section of this module\'s written material. Use "theory" for the ' +
    'concepts and definitions, "tips" for hints the author wrote, and "problem" ' +
    'for the full task statement. Prefer grounding explanations in these over ' +
    'your own general knowledge.',
  parameters: {
    type: 'object',
    properties: {
      section: {
        type: 'string',
        enum: ['problem', 'theory', 'tips'],
        description: 'Which section to read.'
      }
    },
    required: ['section']
  },
  label: (args) => {
    const section = typeof args.section === 'string' ? args.section : 'module';
    return `Reading the ${section} section`;
  },
  run: async (args, ctx) => {
    const requested = typeof args.section === 'string' ? args.section : '';
    // `solution` is deliberately not in the enum, but a model may still try.
    if (requested === 'solution' && !ctx.allowSolutions) {
      return 'The reference solution is withheld on this server. Reason from the theory and tips instead.';
    }
    const allowed = ['problem', 'theory', 'tips'] as const;
    if (!allowed.includes(requested as (typeof allowed)[number])) {
      return `Unknown section "${requested}". Available sections: ${allowed.join(', ')}.`;
    }
    const body = ctx.problem.tabs[requested as (typeof allowed)[number]]?.trim();
    if (!body) return `This module has no "${requested}" section.`;
    return clip(`## ${requested}\n\n${body}`);
  }
};

// ── read_last_run ────────────────────────────────────────────────────────

const readLastRun: ToolDefinition = {
  name: 'read_last_run',
  description:
    'Read the output of the last time the learner pressed Run: stdout, stderr, ' +
    'and whether it errored or timed out. This is the fastest way to diagnose a ' +
    'crash or a wrong result — call it whenever they mention an error.',
  parameters: {
    type: 'object',
    properties: { language: LANGUAGE_PARAM },
    required: []
  },
  label: () => 'Checking your last run',
  run: async (args, ctx) => {
    if (ctx.problem.type !== 'coding') {
      return 'This is not a coding module, so there are no runs to inspect.';
    }
    const language = resolveLanguage(args, ctx);
    await dbReady;
    const rows = await dbAll<{ result: string; timestamp: number | bigint }>(
      `SELECT result, timestamp
         FROM runs
        WHERE user_id = ? AND problem_id = ? AND language = ?`,
      [ctx.userId, ctx.problemId, language]
    );
    if (rows.length === 0) {
      return `The learner has not run their ${language} code yet.`;
    }

    const result = parseJson<RunResult>(rows[0].result);
    if (!result) return 'The last run record could not be read.';

    const when = new Date(Number(rows[0].timestamp)).toISOString();
    const duration = result.durationMs == null ? 'unknown' : `${result.durationMs}ms`;

    return clip(
      [
        `Last ${language} run (${when})`,
        `status: ${result.status}${result.success ? '' : ' (did not finish cleanly)'}`,
        `duration: ${duration}`,
        '',
        describeStream('stdout', result.stdout),
        '',
        describeStream('stderr', result.stderr)
      ].join('\n')
    );
  }
};

// ── read_submission_result ───────────────────────────────────────────────

const readSubmissionResult: ToolDefinition = {
  name: 'read_submission_result',
  description:
    "Read the grader's verdict on the learner's most recent submission, " +
    'including any expected-vs-actual differences. Call this when they ask why ' +
    'a submission was rejected.',
  parameters: {
    type: 'object',
    properties: { language: LANGUAGE_PARAM },
    required: []
  },
  label: () => 'Checking your last submission',
  run: async (args, ctx) => {
    if (ctx.problem.type !== 'coding') {
      return 'This is not a coding module, so there are no submissions to inspect.';
    }
    const language = resolveLanguage(args, ctx);
    await dbReady;
    const rows = await dbAll<{ result: string; timestamp: number | bigint }>(
      `SELECT result, timestamp
         FROM submissions
        WHERE user_id = ? AND problem_id = ? AND language = ?
        ORDER BY timestamp DESC
        LIMIT 1`,
      [ctx.userId, ctx.problemId, language]
    );
    if (rows.length === 0) {
      return `The learner has not submitted any ${language} code yet.`;
    }

    const result = parseJson<SubmitResult>(rows[0].result);
    if (!result) return 'The last submission record could not be read.';

    const when = new Date(Number(rows[0].timestamp)).toISOString();
    const lines = [
      `Last ${language} submission (${when})`,
      `verdict: ${result.verdict}`,
      `score: ${result.score ?? 'not scored'}`,
      `summary: ${result.summary || result.message || '(none)'}`
    ];

    // Newer submissions carry the comparison in structured form; the
    // mismatching lines are the part worth spending tokens on.
    if (result.diff?.length) {
      const bad = result.diff.filter((row) => row.kind !== 'same');
      lines.push(
        '',
        `${bad.length} of ${result.diff.length} output lines differ:`,
        ...bad.slice(0, 40).map((row) => {
          const at = row.expectedNo ?? row.actualNo ?? '?';
          if (row.kind === 'missing') return `  line ${at}: expected "${row.expected}" — the learner printed nothing here`;
          if (row.kind === 'extra')   return `  line ${at}: the learner printed "${row.actual}" — not expected`;
          return `  line ${at}: expected "${row.expected}" but got "${row.actual}"`;
        })
      );
      if (bad.length > 40) lines.push(`  [...${bad.length - 40} more differing lines...]`);
    } else if (result.stderr) {
      lines.push('', describeStream('error output', result.stderr));
    } else {
      // Submissions saved before the structured fields existed.
      for (const test of result.testResults ?? []) {
        lines.push('', `test "${test.name}": ${test.passed ? 'passed' : 'FAILED'}`);
        // Only failing cases are worth the tokens; a pass needs no diff.
        if (!test.passed) {
          if (test.expected) lines.push(describeStream('  expected', test.expected));
          if (test.actual) lines.push(describeStream('  actual', test.actual));
        }
      }
    }

    if (result.verdict === 'pending') {
      lines.push(
        '',
        'Note: "pending" means this module has no deterministic expected output, ' +
          'so the grader could not decide automatically. Judge the code on its merits.'
      );
    }

    return clip(lines.join('\n'));
  }
};

// ── registry ─────────────────────────────────────────────────────────────

const ALL_TOOLS: ToolDefinition[] = [
  readLearnerCode,
  readModuleSection,
  readLastRun,
  readSubmissionResult
];

/**
 * Tools available for a given module. Coding-only tools are withheld from
 * reading/quiz/drill modules so the model isn't tempted to call them.
 */
export function toolsFor(problem: Problem): ToolDefinition[] {
  const codingOnly = new Set(['read_learner_code', 'read_last_run', 'read_submission_result']);
  if (problem.type === 'coding') return ALL_TOOLS;
  return ALL_TOOLS.filter((tool) => !codingOnly.has(tool.name));
}

export function findTool(name: string): ToolDefinition | undefined {
  return ALL_TOOLS.find((tool) => tool.name === name);
}
