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

/** The canonical tab IDs shown in the left instruction pane. */
export type TabId = 'problem' | 'theory' | 'tips';

/** Difficulty classification for a problem. */
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

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
  languages?: Language[];
  defaultLanguage?: Language;
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
  languages: Language[];
  defaultLanguage: Language;
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
  };
  /** Starter code source per language. Empty string if not provided. */
  starterCode: Record<Language, string>;
  /** Previous problem slug in this track, or null if first. */
  prevSlug: string | null;
  /** Next problem slug in this track, or null if last. */
  nextSlug: string | null;
}
