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

/**
 * Line equality used by the diff: exact, or numerically equal within the
 * same tolerance the grader itself applies. Without this, a line that
 * passes the fuzzy check would still be reported as a difference, which
 * reads as the grader contradicting itself.
 */
function linesEqual(a: string, b: string): boolean {
  return a === b || fuzzyMatch(a, b);
}

/**
 * Longest-common-subsequence table over the two line arrays.
 *
 * The previous implementation zipped the two sides positionally, so one
 * missing or extra line at the top made every following line report as
 * changed. LCS keeps the alignment, so a single dropped line shows up as a
 * single dropped line.
 *
 * Cost is O(n·m); outputs here are graded against a fixture and stay small,
 * but we bail out to the positional zip past a generous cap so a runaway
 * program can't turn a failed submission into a multi-second stall.
 */
const LCS_CELL_CAP = 2_000_000;

/**
 * Alignment key for a line: numeric tokens are collapsed to a fixed
 * precision so two lines that the grader would call equal usually hash the
 * same. Only used to line the two sides up — the same/changed verdict on
 * each emitted row still goes through `linesEqual`.
 */
function alignKey(line: string): string {
  return line.replace(new RegExp(NUM_RE.source, 'g'), (m) => {
    const v = parseFloat(m);
    return Number.isFinite(v) ? v.toPrecision(6) : m;
  });
}

function alignLines(expLines: string[], actLines: string[]): Array<[string | undefined, string | undefined]> {
  const n = expLines.length;
  const m = actLines.length;

  if (n * m > LCS_CELL_CAP) {
    const out: Array<[string | undefined, string | undefined]> = [];
    for (let i = 0; i < Math.max(n, m); i++) out.push([expLines[i], actLines[i]]);
    return out;
  }

  const expKeys = expLines.map(alignKey);
  const actKeys = actLines.map(alignKey);

  // lcs[i][j] = length of the LCS of expLines[i..] and actLines[j..]
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = expKeys[i] === actKeys[j]
        ? lcs[i + 1][j + 1] + 1
        : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }

  const out: Array<[string | undefined, string | undefined]> = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (expKeys[i] === actKeys[j]) {
      out.push([expLines[i], actLines[j]]);
      i++;
      j++;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      // Pair a dropped expected line with the actual line sitting opposite
      // it when that one is also about to be reported, so the common
      // "same line, different value" case renders as one changed row
      // instead of a delete followed by an unrelated insert.
      if (j < m && lcs[i + 1][j + 1] === lcs[i + 1][j] && lcs[i + 1][j + 1] === lcs[i][j + 1]) {
        out.push([expLines[i], actLines[j]]);
        i++;
        j++;
      } else {
        out.push([expLines[i], undefined]);
        i++;
      }
    } else {
      out.push([undefined, actLines[j]]);
      j++;
    }
  }
  while (i < n) out.push([expLines[i++], undefined]);
  while (j < m) out.push([undefined, actLines[j++]]);
  return out;
}

/**
 * Unified-style diff string.
 *
 * Format is stable and parsed by the client (`parseGraderDiff`) to build the
 * side-by-side view: a `--- expected` / `+++ actual` header, then one line
 * per row prefixed with `  ` (same), `- ` (expected only) or `+ ` (actual
 * only). Changed rows emit the `-` line immediately followed by the `+`.
 */
export function buildDiff(expected: string, actual: string): string {
  const rows = alignLines(expected.split('\n'), actual.split('\n'));
  const diffLines: string[] = ['--- expected', '+++ actual'];
  for (const [e, a] of rows) {
    if (e !== undefined && a !== undefined && linesEqual(e, a)) {
      diffLines.push(`  ${e}`);
    } else {
      if (e !== undefined) diffLines.push(`- ${e}`);
      if (a !== undefined) diffLines.push(`+ ${a}`);
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
