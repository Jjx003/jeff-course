/**
 * Builds the system prompt that grounds the tutor in the module the learner
 * is currently looking at.
 *
 * SERVER-SIDE ONLY.
 *
 * The prompt is deliberately small: module metadata, the task statement, and
 * an inventory of what can be fetched. Theory, tips, the learner's code, run
 * output, and grader verdicts are all pulled on demand through tools, so a
 * long theory page no longer crowds out the conversation and the editor
 * buffer is not re-uploaded on every turn.
 *
 * Solution walkthroughs, reference solution code, and quiz answer keys are
 * withheld unless TUTOR_ALLOW_SOLUTIONS=1. The tutor is meant to unblock a
 * learner, not to hand over the answer.
 */

import { loadProblem, loadTrack } from '$lib/content/courseLoader.js';
import type { Problem, Track } from '$lib/types/course.js';
import type { TutorAsk } from '$lib/types/tutor.js';
import { readTutorSettings } from './config.js';

/** Per-section cap so a long problem statement can't dominate the prompt. */
const SECTION_CHAR_LIMIT = 6000;
const CODE_CHAR_LIMIT = 8000;

export interface TutorContext {
  track: Track;
  problem: Problem;
  systemPrompt: string;
}

function section(title: string, body: string | undefined, limit = SECTION_CHAR_LIMIT): string {
  const text = (body ?? '').trim();
  if (!text) return '';
  const clipped =
    text.length <= limit ? text : `${text.slice(0, limit)}\n\n[...truncated for length...]`;
  return `\n\n## ${title}\n\n${clipped}`;
}

function describeQuiz(problem: Problem): string {
  const questions = problem.quizQuestions ?? [];
  if (questions.length === 0) return '';
  // Stems only. Correct indices and explanations stay on the server.
  const stems = questions
    .map((q, i) => `${i + 1}. ${(q.stem ?? q.stem_template ?? '').trim()}`)
    .filter((line) => line.length > 3)
    .join('\n');
  return section(`Assessment questions (${questions.length}), answer key withheld`, stems);
}

const BASE_INSTRUCTIONS = `You are the AI tutor built into jeff-course, a self-paced learning app.

You are helping one learner with one specific module. Your job is to build
their understanding, not to complete the work for them.

How to respond:
- Answer the question that was actually asked, directly and in plain language.
- Prefer the shortest explanation that genuinely lands. Skip preamble.
- Ground your explanation in this module's own material and vocabulary. When
  the module already defines a term, use its definition rather than inventing
  a parallel one.
- When the learner is stuck, give the next useful step or a pointed question,
  not the finished answer. Escalate the amount of help if they are still stuck
  after a couple of turns.
- If the learner explicitly and repeatedly asks for the full answer, give it,
  but explain the reasoning so the answer teaches something.
- Use Markdown. Use LaTeX with $...$ or $$...$$ for math. Use fenced code
  blocks with a language tag for code.
- If something falls outside this module's material or you are unsure, say so
  plainly instead of guessing.`;

const TOOL_INSTRUCTIONS = `

How to use your tools:
- You can read this module's theory and tips, the learner's current editor
  buffer, their last run's output, and the grader's last verdict. Only the
  task statement is given to you upfront.
- Look before you answer. If they ask about their code, read it first rather
  than guessing at what they wrote. If they mention an error, read the last
  run. Do not ask them to paste something you can fetch yourself.
- Do not narrate your tool use ("let me check..."). The learner already sees
  which tools ran. Just answer once you know.
- Call several tools at once when you need several things.
- If a tool reports that the learner has not written or run anything yet, say
  so plainly and help them make a start.`;

const WITHHOLD_SOLUTIONS = `
- The reference solution and assessment answer key are deliberately not
  available to you, through tools or otherwise. Do not pretend to quote them;
  reason from the module material instead.`;

const ALLOW_SOLUTIONS = `
- The reference solution is included below. Still default to hints; reveal it
  only when the learner clearly asks for the full answer.`;

/**
 * Assemble the grounding prompt for a module. Returns null when the track or
 * module does not exist.
 */
export async function buildTutorContext(
  trackSlug: string,
  problemSlug: string,
  ask: TutorAsk
): Promise<TutorContext | null> {
  const [track, problem] = await Promise.all([
    loadTrack(trackSlug),
    loadProblem(trackSlug, problemSlug)
  ]);
  if (!track || !problem) return null;

  const { allowSolutions } = readTutorSettings();

  let prompt =
    BASE_INSTRUCTIONS + (allowSolutions ? ALLOW_SOLUTIONS : WITHHOLD_SOLUTIONS) + TOOL_INSTRUCTIONS;

  prompt += `\n\n# Current module\n\nCourse: ${track.title} — ${track.description}
Module: ${problem.title} (${problem.type}, ${problem.difficulty})
Summary: ${problem.description}`;

  if (problem.type === 'coding') {
    const languages = (problem.languages ?? []).join(', ') || 'none';
    prompt += `\nLanguages offered: ${languages}. The learner currently has ${
      ask.language ?? problem.defaultLanguage ?? 'unknown'
    } open.`;
  }

  prompt += section('Task statement', problem.tabs.problem);
  prompt += describeQuiz(problem);

  // Advertise what is fetchable so the model doesn't claim it lacks context.
  const available: string[] = [];
  if (problem.tabs.theory?.trim()) available.push('theory');
  if (problem.tabs.tips?.trim()) available.push('tips');
  if (available.length > 0) {
    prompt += `\n\nFetchable sections for this module: ${available.join(
      ', '
    )}. Read them with read_module_section rather than guessing at their contents.`;
  }

  if (allowSolutions) {
    prompt += section('Reference solution walkthrough', problem.tabs.solution);
    for (const lang of problem.languages ?? []) {
      const code = problem.solutionCode?.[lang];
      if (code) prompt += section(`Reference solution (${lang})`, '```\n' + code + '\n```', CODE_CHAR_LIMIT);
    }
  }

  if (ask.activeTab) {
    prompt += `\n\nThe learner is currently reading the "${ask.activeTab}" tab.`;
  }

  return { track, problem, systemPrompt: prompt };
}
