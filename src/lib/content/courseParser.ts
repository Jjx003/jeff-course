/**
 * courseParser.ts
 *
 * Reads the `courses/` directory on disk and converts raw YAML + Markdown
 * files into normalized `Track` and `Problem` app models.
 *
 * This module runs SERVER-SIDE ONLY (inside +page.server.ts load functions).
 * It uses Node.js `fs` and `path` directly.
 *
 * Extension point: if courses are later served from a CMS or remote API,
 * replace this module with a remote implementation behind the
 * `CourseRepository` interface. UI components never call this directly.
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

import type {
  Track,
  Problem,
  ProblemMeta,
  RawCourseYaml,
  RawModuleYaml,
  Language,
  Difficulty,
  ModuleType
} from '$lib/types/course.js';

// ── Helpers ──────────────────────────────────────────────────────────────

function readFileOrEmpty(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return '';
  }
}

function readYaml<T>(filePath: string): T | null {
  const raw = readFileOrEmpty(filePath);
  if (!raw.trim()) return null;
  try {
    return yaml.load(raw) as T;
  } catch (err) {
    console.warn(`[courseParser] Failed to parse YAML at ${filePath}:`, err);
    return null;
  }
}

function normalizeDifficulty(value: string | undefined): Difficulty {
  const valid: Difficulty[] = ['beginner', 'intermediate', 'advanced'];
  return valid.includes(value as Difficulty) ? (value as Difficulty) : 'beginner';
}

function normalizeLanguages(values: string[] | undefined): Language[] {
  const valid: Language[] = ['python', 'cpp'];
  if (!values || values.length === 0) return ['python'];
  return values.filter((v) => valid.includes(v as Language)) as Language[];
}

function normalizeModuleType(value: string | undefined): ModuleType {
  return value === 'reading' ? 'reading' : 'coding';
}

// ── Module (problem) parsing ─────────────────────────────────────────────

/**
 * Parse a single module directory into a `ProblemMeta`.
 * Returns null if the directory is missing required files.
 */
function parseModuleMeta(
  modulePath: string,
  trackSlug: string,
  order: number
): ProblemMeta | null {
  const metaPath = path.join(modulePath, 'module.yaml');
  const raw = readYaml<RawModuleYaml>(metaPath);
  if (!raw) {
    console.warn(`[courseParser] Skipping ${modulePath}: missing or invalid module.yaml`);
    return null;
  }

  const type = normalizeModuleType(raw.type);
  const languages = normalizeLanguages(raw.languages);
  const defaultLanguage: Language = languages.includes(raw.defaultLanguage as Language)
    ? (raw.defaultLanguage as Language)
    : languages[0];

  return {
    slug: raw.slug,
    trackSlug,
    title: raw.title,
    description: raw.description ?? '',
    order: raw.order ?? order,
    difficulty: normalizeDifficulty(raw.difficulty),
    estimatedMinutes: raw.estimatedMinutes ?? 30,
    tags: raw.tags ?? [],
    type,
    languages,
    defaultLanguage
  };
}

/**
 * Parse the full problem: metadata + markdown tabs + starter code.
 */
export function parseFullProblem(
  modulePath: string,
  trackSlug: string,
  order: number,
  prevSlug: string | null,
  nextSlug: string | null
): Problem | null {
  const meta = parseModuleMeta(modulePath, trackSlug, order);
  if (!meta) return null;

  const solutionMd = readFileOrEmpty(path.join(modulePath, 'solution.md'));
  const tabs = {
    problem: readFileOrEmpty(path.join(modulePath, 'problem.md')),
    theory:  readFileOrEmpty(path.join(modulePath, 'theory.md')),
    tips:    readFileOrEmpty(path.join(modulePath, 'tips.md')),
    ...(solutionMd.trim() ? { solution: solutionMd } : {})
  };

  const starterCode: Record<Language, string> = {
    python: readFileOrEmpty(path.join(modulePath, 'starter', 'python.py')),
    cpp:    readFileOrEmpty(path.join(modulePath, 'starter', 'cpp.cpp'))
  };

  // Optional: solution code per language (solution/python.py, solution/cpp.cpp)
  const solutionCode: Partial<Record<Language, string>> = {};
  const langSolutionMap: Record<Language, string> = { python: 'python.py', cpp: 'cpp.cpp' };
  for (const lang of ['python', 'cpp'] as Language[]) {
    const solPath = path.join(modulePath, 'solution', langSolutionMap[lang]);
    if (fs.existsSync(solPath)) {
      const content = readFileOrEmpty(solPath).trim();
      if (content) solutionCode[lang] = content;
    }
  }
  const hasSolutionCode = Object.keys(solutionCode).length > 0;

  // Optional: requirements.txt for UV-based Python dependency management
  const requirementsTxtPath = path.join(modulePath, 'requirements.txt');
  const requirementsPath = fs.existsSync(requirementsTxtPath)
    ? requirementsTxtPath
    : undefined;

  // Optional: expected_output/<lang>.txt for grading
  const expectedOutput: Partial<Record<Language, string>> = {};
  const languages: Language[] = ['python', 'cpp'];
  const langFileMap: Record<Language, string> = { python: 'python.txt', cpp: 'cpp.txt' };
  for (const lang of languages) {
    const outPath = path.join(modulePath, 'expected_output', langFileMap[lang]);
    if (fs.existsSync(outPath)) {
      const content = readFileOrEmpty(outPath).trim();
      if (content) {
        expectedOutput[lang] = content;
      }
    }
  }
  const hasExpectedOutput = Object.keys(expectedOutput).length > 0;

  return {
    ...meta,
    tabs,
    starterCode,
    prevSlug,
    nextSlug,
    ...(requirementsPath ? { requirementsPath } : {}),
    ...(hasExpectedOutput ? { expectedOutput: expectedOutput as Record<Language, string> } : {}),
    ...(hasSolutionCode ? { solutionCode } : {})
  };
}

// ── Track parsing ────────────────────────────────────────────────────────

/**
 * Parse a single track directory into a `Track` (with ProblemMeta list).
 */
export function parseTrack(trackPath: string): Track | null {
  const metaPath = path.join(trackPath, 'course.yaml');
  const raw = readYaml<RawCourseYaml>(metaPath);
  if (!raw) {
    console.warn(`[courseParser] Skipping ${trackPath}: missing or invalid course.yaml`);
    return null;
  }

  // Find module directories: any subdirectory containing module.yaml,
  // sorted alphabetically (so numeric prefixes like 01-, 02- give order).
  const entries = fs.readdirSync(trackPath, { withFileTypes: true });
  const moduleDirs = entries
    .filter((e: import('fs').Dirent) => e.isDirectory())
    .map((e: import('fs').Dirent) => e.name)
    .sort()
    .filter((name: string) => {
      const moduleYaml = path.join(trackPath, name, 'module.yaml');
      return fs.existsSync(moduleYaml);
    });

  const problems: ProblemMeta[] = moduleDirs
    .map((dirName: string, idx: number) => parseModuleMeta(path.join(trackPath, dirName), raw.slug, idx + 1))
    .filter((p: ProblemMeta | null): p is ProblemMeta => p !== null);

  return {
    slug: raw.slug,
    title: raw.title,
    description: raw.description,
    tags: raw.tags ?? [],
    difficulty: normalizeDifficulty(raw.difficulty),
    order: raw.order ?? 1,
    problems
  };
}

// ── Top-level course directory scan ──────────────────────────────────────

/**
 * Scan the root `coursesDir` for all tracks.
 * Returns tracks sorted by their `order` field.
 */
export function parseAllTracks(coursesDir: string): Track[] {
  if (!fs.existsSync(coursesDir)) {
    console.warn(`[courseParser] courses directory not found at ${coursesDir}`);
    return [];
  }

  const entries = fs.readdirSync(coursesDir, { withFileTypes: true });
  const trackDirs = entries
    .filter((e: import('fs').Dirent) => e.isDirectory())
    .map((e: import('fs').Dirent) => path.join(coursesDir, e.name));

  const tracks = trackDirs
    .map((dir: string) => parseTrack(dir))
    .filter((t: Track | null): t is Track => t !== null)
    .sort((a: Track, b: Track) => a.order - b.order);

  return tracks;
}

/**
 * Resolve the filesystem path for a specific module directory within a track.
 * Used to load a specific problem on demand.
 */
export function resolveModulePath(
  coursesDir: string,
  trackSlug: string,
  problemSlug: string
): string | null {
  const trackPath = path.join(coursesDir, trackSlug);
  if (!fs.existsSync(trackPath)) return null;

  const entries = fs.readdirSync(trackPath, { withFileTypes: true });
  const moduleDirs = entries
    .filter((e: import('fs').Dirent) => e.isDirectory())
    .sort((a: import('fs').Dirent, b: import('fs').Dirent) => a.name.localeCompare(b.name));

  for (const dir of moduleDirs) {
    const moduleYamlPath = path.join(trackPath, dir.name, 'module.yaml');
    if (!fs.existsSync(moduleYamlPath)) continue;

    const raw = readYaml<RawModuleYaml>(moduleYamlPath);
    if (raw?.slug === problemSlug) {
      return path.join(trackPath, dir.name);
    }
  }
  return null;
}
