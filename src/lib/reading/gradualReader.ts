export interface GradualReadStep {
  id: string;
  sectionId: string;
  sectionLabel: string;
  headingIds: string[];
  title: string;
  content: string;
}

interface ReadingSection {
  id: string;
  label: string;
  content: string;
}

const TARGET_CHARS = 760;
const MAX_CHARS = 1180;
const MIN_STANDALONE_CHARS = 140;

function isThematicBreak(block: string): boolean {
  return /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/.test(block.trim());
}

function hasRichAtomicBlock(blocks: string[]): boolean {
  return blocks.some((block) => {
    const trimmed = block.trim();
    return (
      trimmed.startsWith('```') ||
      trimmed.startsWith('~~~') ||
      trimmed.startsWith('$$') ||
      isMarkdownTableBlock(block)
    );
  });
}

function isMarkdownTableRow(line: string): boolean {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && (trimmed.match(/\|/g)?.length ?? 0) >= 2;
}

function isMarkdownTableSeparator(line: string): boolean {
  const cells = line
    .trim()
    .replace(/^\||\|$/g, '')
    .split('|')
    .map((cell) => cell.trim());
  return cells.length >= 2 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function isMarkdownTableBlock(block: string): boolean {
  const lines = block.split('\n').filter((line) => line.trim().length > 0);
  return lines.length >= 2 && isMarkdownTableRow(lines[0]) && isMarkdownTableSeparator(lines[1]);
}

function splitLongListBlock(block: string): string[] {
  if (block.length <= MAX_CHARS) return [block];

  const lines = block.split('\n');
  const chunks: string[] = [];
  let current: string[] = [];

  function startsTopLevelListItem(line: string): boolean {
    return /^ {0,3}(?:[-*+]\s+|\d+[.)]\s+)/.test(line);
  }

  function flush() {
    const chunk = current.join('\n').trim();
    if (chunk) chunks.push(chunk);
    current = [];
  }

  for (const line of lines) {
    if (startsTopLevelListItem(line) && current.join('\n').length >= TARGET_CHARS) {
      flush();
    }
    current.push(line);
  }

  flush();
  return chunks.length > 1 ? chunks : [block];
}

function splitMarkdownBlocks(markdown: string): string[] {
  const blocks: string[] = [];
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  let current: string[] = [];
  let inFence = false;
  let inMath = false;

  function flush() {
    const block = current.join('\n').trim();
    if (block) blocks.push(block);
    current = [];
  }

  for (const line of lines) {
    const trimmed = line.trim();
    const startsFence = trimmed.startsWith('```') || trimmed.startsWith('~~~');
    const isMathFence = trimmed === '$$';
    const startsHeading = /^#{1,4}\s+\S/.test(trimmed);

    if (!inFence && !inMath && trimmed === '') {
      flush();
      continue;
    }

    if (!inFence && !inMath && startsHeading) {
      flush();
      blocks.push(line.trim());
      continue;
    }

    current.push(line);

    if (startsFence && !inMath) inFence = !inFence;
    if (isMathFence && !inFence) inMath = !inMath;
  }

  flush();
  return blocks;
}

function isHeading(block: string): boolean {
  return /^#{1,4}\s+\S/.test(block.trim());
}

function slugify(text: string): string {
  const slug = text
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[`*_~[\]()]/g, '')
    .replace(/&[a-z0-9#]+;/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'section';
}

function cleanHeading(text: string): string {
  return text
    .replace(/!\[[^\]]*]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)]\([^)]*\)/g, '$1')
    .replace(/[`*_~]/g, '')
    .replace(/#+\s*$/g, '')
    .trim();
}

function headingText(block: string): string {
  return cleanHeading(
    block
      .trim()
    .replace(/^#{1,6}\s+/, '')
    .replace(/\s+#+$/, '')
  );
}

function nextHeadingId(sectionId: string, text: string, seen: Map<string, number>): string {
  const base = `${sectionId}-${slugify(text)}`;
  const count = seen.get(base) ?? 0;
  seen.set(base, count + 1);
  return count === 0 ? base : `${base}-${count + 1}`;
}

function createStep(
  steps: GradualReadStep[],
  section: ReadingSection,
  title: string,
  headingIds: string[],
  blocks: string[]
) {
  const content = blocks.join('\n\n').trim();
  if (!content) return;
  steps.push({
    id: `${section.id}-${steps.length + 1}`,
    sectionId: section.id,
    sectionLabel: section.label,
    headingIds,
    title,
    content
  });
}

export function buildGradualReadSteps(sections: ReadingSection[]): GradualReadStep[] {
  const steps: GradualReadStep[] = [];

  for (const section of sections) {
    const rawBlocks = splitMarkdownBlocks(section.content);
    const seenHeadings = new Map<string, number>();
    let pending: string[] = [];
    let pendingHeadingIds: string[] = [];
    let currentTitle = section.label;
    let currentLength = 0;

    function flush() {
      createStep(steps, section, currentTitle, pendingHeadingIds, pending);
      pending = [];
      pendingHeadingIds = [];
      currentLength = 0;
    }

    for (const block of rawBlocks) {
      if (isThematicBreak(block)) continue;

      if (isHeading(block)) {
        if (
          pending.length > 0 &&
          (currentLength >= MIN_STANDALONE_CHARS || hasRichAtomicBlock(pending))
        ) {
          flush();
        }
        const text = headingText(block) || section.label;
        currentTitle = text;
        pendingHeadingIds.push(nextHeadingId(section.id, text, seenHeadings));
        continue;
      }

      if (isMarkdownTableBlock(block)) {
        if (pending.length > 0) flush();
        pending.push(block);
        currentLength = block.length;
        flush();
        continue;
      }

      for (const chunk of splitLongListBlock(block)) {
        const nextLength = currentLength + chunk.length;
        if (pending.length > 0 && currentLength >= TARGET_CHARS && nextLength > MAX_CHARS) {
          flush();
        }

        pending.push(chunk);
        currentLength += chunk.length;
      }
    }

    flush();
  }

  for (let i = steps.length - 1; i > 0; i--) {
    const step = steps[i];
    if (
      step.sectionId !== steps[i - 1].sectionId ||
      step.content.length >= MIN_STANDALONE_CHARS ||
      hasRichAtomicBlock([step.content])
    ) {
      continue;
    }
    steps[i - 1] = {
      ...steps[i - 1],
      headingIds: [...steps[i - 1].headingIds, ...step.headingIds],
      content: `${steps[i - 1].content}\n\n${step.content}`.trim()
    };
    steps.splice(i, 1);
  }

  return steps;
}
