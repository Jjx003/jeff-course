/**
 * Output grading — exact + fuzzy numeric comparison used by both the
 * legacy `submitCode` path in `executor.ts` and the new sandbox session
 * pipeline.
 *
 * The fuzzy comparison treats numeric tokens with an absolute-or-relative
 * tolerance of 1e-3 (matching numpy.allclose defaults) so floating-point
 * solutions don't false-fail on machine-epsilon differences. Non-numeric
 * tokens must match exactly.
 *
 * SERVER-SIDE ONLY.
 */

export interface GradeResult {
  passed: boolean;
  /** Unified-style diff string (only present when !passed). */
  diff?: string;
}

/** Trim trailing whitespace per line, then trim the whole string. */
export function normalizeOutput(s: string): string {
  return s
    .split('\n')
    .map((line) => line.trimEnd())
    .join('\n')
    .trim();
}

const NUM_RE = /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g;

interface Token { isNum: boolean; text: string; num?: number }

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  let last = 0;
  for (const m of line.matchAll(new RegExp(NUM_RE.source, 'g'))) {
    const start = m.index!;
    if (start > last) tokens.push({ isNum: false, text: line.slice(last, start) });
    tokens.push({ isNum: true, text: m[0], num: parseFloat(m[0]) });
    last = start + m[0].length;
  }
  if (last < line.length) tokens.push({ isNum: false, text: line.slice(last) });
  return tokens;
}

export function fuzzyMatch(expected: string, actual: string, epsilon = 1e-3): boolean {
  const expLines = expected.split('\n');
  const actLines = actual.split('\n');
  if (expLines.length !== actLines.length) return false;

  for (let i = 0; i < expLines.length; i++) {
    const eLine = expLines[i];
    const aLine = actLines[i];
    if (eLine === aLine) continue;

    const eTokens = tokenizeLine(eLine);
    const aTokens = tokenizeLine(aLine);
    if (eTokens.length !== aTokens.length) return false;

    for (let j = 0; j < eTokens.length; j++) {
      const et = eTokens[j];
      const at = aTokens[j];
      if (et.isNum && at.isNum) {
        const ev = et.num!;
        const av = at.num!;
        const absDiff = Math.abs(av - ev);
        const relDiff = Math.abs(ev) > 1e-10 ? absDiff / Math.abs(ev) : absDiff;
        if (absDiff > epsilon && relDiff > epsilon) return false;
      } else if (et.text !== at.text) {
        return false;
      }
    }
  }
  return true;
}

export function buildDiff(expected: string, actual: string): string {
  const expLines = expected.split('\n');
  const actLines = actual.split('\n');
  const maxLen = Math.max(expLines.length, actLines.length);
  const diffLines: string[] = ['--- expected', '+++ actual'];
  for (let i = 0; i < maxLen; i++) {
    const e = expLines[i];
    const a = actLines[i];
    if (e === undefined) diffLines.push(`+ ${a}`);
    else if (a === undefined) diffLines.push(`- ${e}`);
    else if (e === a) diffLines.push(`  ${e}`);
    else {
      diffLines.push(`- ${e}`);
      diffLines.push(`+ ${a}`);
    }
  }
  return diffLines.join('\n');
}

/**
 * Compare actual stdout against the expected output string. Returns
 * { passed, diff? } — caller decides what verdict / message to set.
 */
export function gradeOutput(expected: string, actual: string): GradeResult {
  const normExp = normalizeOutput(expected);
  const normAct = normalizeOutput(actual);
  if (normExp === normAct || fuzzyMatch(normExp, normAct)) {
    return { passed: true };
  }
  return { passed: false, diff: buildDiff(normExp, normAct) };
}
