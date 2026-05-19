/**
 * Adds lightweight structure around theorem/proof paragraphs after markdown is
 * converted to HTML. Course authors can keep writing ordinary Markdown such as
 * `**Theorem:** ...` and `**Proof:** ...`; the renderer upgrades those blocks
 * into readable mathematical callouts.
 */

const STATEMENT_LABELS = [
  'theorem',
  'lemma',
  'corollary',
  'proposition',
  'definition',
  'claim',
  'example'
];

const PROOF_LABELS = ['proof', 'proof strategy', 'proof of existence', 'proof of uniqueness'];

type HastNode = {
  type?: string;
  tagName?: string;
  value?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
};

function textContent(node: HastNode | undefined): string {
  if (!node) return '';
  if (node.type === 'text') return node.value ?? '';
  return (node.children ?? []).map(textContent).join('');
}

function firstText(node: HastNode): string {
  const first = node.children?.[0];
  if (!first) return '';
  return textContent(first).trim();
}

function normalizedLabel(text: string): string | null {
  const match = text.match(/^([A-Za-z ]+(?:\s+\d+)?(?:\s*\([^)]+\))?)\s*:/);
  if (!match) return null;
  return match[1].replace(/\s+\d+$/, '').replace(/\s*\([^)]+\)$/, '').trim().toLowerCase();
}

function paragraphLabel(node: HastNode): string | null {
  if (node.tagName !== 'p') return null;
  const first = node.children?.[0];
  if (!first) return null;
  if (first.tagName === 'strong') return normalizedLabel(firstText(node));
  if (first.type === 'text') return normalizedLabel(first.value ?? '');
  return null;
}

function isStatementParagraph(node: HastNode): boolean {
  const label = paragraphLabel(node);
  return label ? STATEMENT_LABELS.includes(label) : false;
}

function isProofParagraph(node: HastNode): boolean {
  const label = paragraphLabel(node);
  return label ? PROOF_LABELS.includes(label) : false;
}

function classNames(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String);
  if (typeof value === 'string') return value.split(/\s+/).filter(Boolean);
  return [];
}

function addClass(node: HastNode, ...names: string[]) {
  node.properties ??= {};
  const next = new Set([...classNames(node.properties.className), ...names]);
  node.properties.className = Array.from(next);
}

function statementKind(label: string | null): string {
  if (!label) return 'statement';
  if (label === 'definition') return 'definition';
  if (label === 'example') return 'example';
  return 'statement';
}

function transformChildren(parent: HastNode) {
  if (!parent.children?.length) return;

  const next: HastNode[] = [];
  for (let i = 0; i < parent.children.length; i += 1) {
    const child = parent.children[i];

    if (isStatementParagraph(child)) {
      const label = paragraphLabel(child);
      child.tagName = 'div';
      addClass(child, 'math-statement', `math-statement-${statementKind(label)}`);
      next.push(child);
      continue;
    }

    if (isProofParagraph(child)) {
      child.tagName = 'div';
      addClass(child, 'math-proof');
      next.push(child);
      continue;
    }

    next.push(child);
  }

  parent.children = next;
  for (const child of parent.children) transformChildren(child);
}

export function rehypeProofBlocks() {
  return (tree: HastNode) => {
    transformChildren(tree);
  };
}
