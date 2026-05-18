/**
 * Core domain types for the course content model.
 *
 * These types are the normalized representation produced by the course parser
 * and consumed by UI components. They are intentionally decoupled from the
 * raw filesystem format (YAML + Markdown) so the parser can evolve
 * independently of the UI.
 *
 * Future: a remote CMS/API implementation would produce the same types.
 */

/** Supported editor languages. Extend here to add more. */
export type Language = 'python' | 'cpp';

import type { SandboxMode, ResourceLimits } from './sandbox.js';

/**
 * Optional per-module hint for the sandbox runtime. When present, the
 * problem page uses these as fallback defaults for new visitors who don't
 * have a per-track preference saved yet. Course authors can use this to
 * nudge users toward, say, "Container + GPU" for a training exercise.
 */
export interface RuntimeHint {
  recommendedMode?: SandboxMode;
  resources?: Partial<ResourceLimits>;
}

/** The canonical tab IDs shown in the left instruction pane. */
export type TabId = 'problem' | 'theory' | 'tips' | 'solution';

/** Difficulty classification for a problem. */
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

/**
 * The kind of module:
 *   - `coding`  : standard split-pane exercise with a code editor (default).
 *   - `reading` : full-width textbook-style page (no editor, no runner). Use
 *                 for theory, background concepts, or pure-reading lessons.
 */
export type ModuleType = 'coding' | 'reading';

// ── Raw filesystem metadata shapes (used by the parser) ─────────────────

/**
 * Shape of `course.yaml` on disk.
 * The parser reads this and converts it to `Track`.
 */
export interface RawCourseYaml {
  title: string;
  slug: string;
  description: string;
  tags?: string[];
  difficulty?: Difficulty;
  order?: number;
}

/**
 * Shape of `module.yaml` on disk.
 * The parser reads this and converts it to `Problem`.
 */
export interface RawModuleYaml {
  title: string;
  slug: string;
  description?: string;
  order?: number;
  difficulty?: Difficulty;
  estimatedMinutes?: number;
  tags?: string[];
  /** Defaults to `coding` when omitted. */
  type?: ModuleType;
  languages?: Language[];
  defaultLanguage?: Language;
  /** Optional sandbox runtime hint (recommended mode + default resources). */
  runtime?: RuntimeHint;
}

// ── Normalized app models ────────────────────────────────────────────────

/**
 * A "track" is the top-level grouping (e.g. "Tensors", "Matrix Multiplication").
 * Each track contains an ordered list of problems.
 */
export interface Track {
  slug: string;
  title: string;
  description: string;
  tags: string[];
  difficulty: Difficulty;
  order: number;
  /** Ordered list of problem slugs belonging to this track. */
  problems: ProblemMeta[];
}

/**
 * Lightweight metadata for a problem used in lists and navigation.
 * Does not include the heavy markdown content.
 */
export interface ProblemMeta {
  slug: string;
  trackSlug: string;
  title: string;
  description: string;
  order: number;
  difficulty: Difficulty;
  estimatedMinutes: number;
  tags: string[];
  /** `coding` (split pane + editor) or `reading` (textbook layout). */
  type: ModuleType;
  languages: Language[];
  defaultLanguage: Language;
  /** Optional sandbox runtime hint authored in module.yaml. */
  runtime?: RuntimeHint;
}

/**
 * Full problem data including rendered tab content and starter code.
 * Loaded on demand when the user navigates to a specific problem.
 */
export interface Problem extends ProblemMeta {
  /** Raw markdown source for each tab. Rendering happens client-side. */
  tabs: {
    problem: string;
    theory: string;
    tips: string;
    /** Solution walkthrough markdown. Absent if no solution.md exists. */
    solution?: string;
  };
  /** Starter code source per language. Empty string if not provided. */
  starterCode: Record<Language, string>;
  /** Full solution code per language. Absent if no solution/ dir exists. */
  solutionCode?: Partial<Record<Language, string>>;
  /** Previous problem slug in this track, or null if first. */
  prevSlug: string | null;
  /** Next problem slug in this track, or null if last. */
  nextSlug: string | null;
  /** Absolute path to requirements.txt if present (used by executor). */
  requirementsPath?: string;
  /** Pre-computed expected stdout per language (from expected_output/<lang>.txt). */
  expectedOutput?: Record<Language, string>;
}
