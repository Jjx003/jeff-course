# agents.md — Agent Onboarding Guide

> **Keep this file up to date.** If you make a significant structural change (new route, new service interface, new course content format, new dependency, new deployment target), update the relevant section before finishing your work.

---

## Project Purpose

**jeff-course** is a local-first, LeetCode-style platform for learning machine learning and deep learning through structured coding exercises and reading material. It is filesystem-driven — all course content lives in `courses/` as YAML + Markdown files. No database is required to run it.

The owner (Jeff) uses an agent to author new courses on demand: given a subject area, an agent writes the full course content (YAML metadata, Markdown explanations, starter code). The platform is designed to be extended to a production backend later without touching the UI layer.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | SvelteKit 2 + Svelte 5 (runes syntax) |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS v3 + `@tailwindcss/typography` |
| Code editor | Monaco Editor (dynamic import, no-op blob worker) |
| Markdown/Math | unified → remark → rehype → KaTeX (rehype-katex) |
| Diagrams | `mermaid` (client-side render to inline SVG) |
| Course parsing | js-yaml + Node.js `fs` (server-side only) |
| Deployment | `@sveltejs/adapter-node` |
| Build tool | Vite 6.x |

**Critical version constraint:** `@sveltejs/vite-plugin-svelte` must be **v5+** for Vite 6 compatibility. v4 peer-requires Vite ^5 and causes `css is not a function` SSR errors in dev mode.

---

## Directory Layout

```
jeff-course/
├── agents.md                    # ← this file
├── README.md
├── package.json
├── svelte.config.js             # adapter-node
├── vite.config.ts               # Monaco optimizeDeps, allows courses/ serving
├── tailwind.config.js           # custom surface/accent palette + typography plugin
├── postcss.config.cjs           # Tailwind + autoprefixer (must be .cjs even with "type": "module")
│
├── courses/                     # All course content — filesystem-driven
│   └── <track-slug>/
│       ├── course.yaml          # Track metadata
│       └── <NN>-<problem-slug>/
│           ├── module.yaml      # Problem metadata (includes `type: reading | coding`)
│           ├── problem.md       # Problem statement / reading body
│           ├── theory.md        # Theory/explanation
│           ├── tips.md          # Hints
│           ├── solution.md      # optional: walkthrough of the reference solution
│           ├── starter/         # coding modules only
│           │   ├── python.py
│           │   └── cpp.cpp
│           ├── solution/        # optional: reference solution code
│           │   ├── python.py
│           │   └── cpp.cpp
│           ├── requirements.txt         # optional: UV pip deps
│           └── expected_output/         # optional: grading reference (omit for non-deterministic output)
│               ├── python.txt
│               └── cpp.txt
│
└── src/
    ├── app.html
    ├── app.css                  # KaTeX @import MUST come before @tailwind directives
    ├── lib/
    │   ├── types/
    │   │   ├── course.ts        # Track, Problem, ProblemMeta, Language, Difficulty
    │   │   └── execution.ts     # RunRequest, RunResult, Draft, RunSnapshot, SubmitSnapshot
    │   ├── content/             # SERVER-SIDE ONLY (uses Node.js fs)
    │   │   ├── courseParser.ts  # Parse YAML/MD → domain models
    │   │   └── courseLoader.ts  # Facade: reads COURSES_DIR env var
    │   ├── markdown/
    │   │   └── renderMarkdown.ts  # unified pipeline (async + sync)
    │   ├── services/
    │   │   ├── courseRepository.ts    # interface
    │   │   ├── draftStorage.ts        # interface
    │   │   ├── runHistoryStorage.ts   # interface
    │   │   ├── submissionStorage.ts   # interface
    │   │   ├── executionService.ts    # interface
    │   │   ├── index.ts               # service registry (dependency injection)
    │   │   └── local/                 # localStorage + mock implementations
    │   │       ├── courseRepository.local.ts
    │   │       ├── draftStorage.local.ts
    │   │       ├── runHistoryStorage.local.ts
    │   │       ├── submissionStorage.local.ts
    │   │       └── executionService.local.ts  # POSTs to /api/execute (real execution)
    │   └── components/
    │       ├── Header.svelte
    │       ├── SplitPane.svelte
    │       ├── TabGroup.svelte
    │       ├── MarkdownRenderer.svelte
    │       ├── CodeEditor.svelte
    │       ├── LanguageSwitcher.svelte
    │       ├── OutputPanel.svelte
    │       └── ProblemNav.svelte
    └── routes/
        ├── +layout.svelte
        ├── +page.svelte                                      # Landing page
        ├── tracks/
        │   ├── +page.svelte                                  # All tracks grid
        │   ├── +page.server.ts
        │   └── [trackSlug]/
        │       ├── +page.svelte                              # Track detail + problem list
        │       ├── +page.server.ts
        │       └── problems/[problemSlug]/
        │               ├── +page.svelte                      # Main exercise (split pane)
        │               └── +page.server.ts
```

---

## Course Content Format

### Track (`courses/<track-slug>/course.yaml`)
```yaml
title: "Introduction to Tensors"
slug: "tensors"
description: "Build tensor primitives from scratch."
tags: [machine-learning, linear-algebra]
difficulty: intermediate   # beginner | intermediate | advanced
order: 1
```

### Problem (`courses/<track-slug>/<NN>-<problem-slug>/module.yaml`)
```yaml
title: "Tensor Basics: Shape and Strides"
slug: "intro-to-tensors"
description: "Create a minimal Tensor class."
order: 1
difficulty: beginner
estimatedMinutes: 25
tags: [tensors, numpy]
type: coding              # 'coding' | 'reading'
languages: [python, cpp]  # CODING only — omit for reading modules
defaultLanguage: python   # CODING only — omit for reading modules
```

The `<NN>-` numeric prefix in the directory name controls sort order within a track. The `slug` field in `module.yaml` is what appears in the URL.

### Module types

`type: coding` (the default) is the original behaviour: an editor pane plus run/submit grading against optional `expected_output/`. The module folder must contain `starter/`, and may contain `requirements.txt` and `expected_output/` for grading.

`type: reading` is a textbook-style module: no editor, no run/submit, just `problem.md` + `theory.md` + `tips.md` rendered with KaTeX and Mermaid. Reading modules MUST omit `languages` and `defaultLanguage`. They MUST NOT have a `starter/` directory; if one exists the parser ignores it. Use reading modules for conceptual deep-dives between coding exercises.

### Markdown files
All three Markdown files (`problem.md`, `theory.md`, `tips.md`) support:
- GitHub Flavored Markdown (tables, task lists, strikethrough)
- Inline LaTeX: `$C_{ij} = \sum_k A_{ik} B_{kj}$`
- Block LaTeX: `$$\text{stride}_i = \prod_{j=i+1}^{k-1} d_j$$`
- Mermaid diagrams in ` ```mermaid ` fences — rendered to inline SVG client-side via the `mermaid` package. The renderer fails gracefully (renders as a code block) if the package fails to load, so old browsers don't break the page.

Mermaid syntax notes when authoring: no spaces in node IDs, quote labels containing parentheses or special characters, and avoid `style` / `classDef` directives (they don't reliably render with our default theme). See `courses/protein-folding/02-protein-structure/problem.md` and `04-folding-problem/problem.md` for examples.

### Figure convention
Course-bundled images live at `static/courses/<track-slug>/<image>.png` and are referenced from Markdown as `![alt](/courses/<track-slug>/<image>.png)`. SvelteKit serves the `static/` directory at the site root, so the leading `/courses/...` URL works in both dev and production. External URLs (RCSB PDB, Wikipedia Commons, etc.) work for public-domain figures and don't need to be bundled.

### Starter code (coding modules only)
`starter/python.py` and `starter/cpp.cpp` — the code the user sees when first opening a problem. Should compile/run cleanly as a skeleton (with TODOs or `pass`/stubs, not blank files).

---

## Service Architecture

All services follow an **interface + local implementation** pattern to allow clean backend swaps later.

```
src/lib/services/
  <name>.ts                 ← TypeScript interface only
  local/<name>.local.ts     ← Implementation (localStorage or mock)
  index.ts                  ← Registry: exports the active implementation
```

### Current local implementations

| Service | Storage | Notes |
|---|---|---|
| `CourseRepository` | Node.js `fs` | SERVER-SIDE ONLY via `+page.server.ts` |
| `DraftStorage` | localStorage | Key: `draft::{problemId}::{language}` |
| `RunHistoryStorage` | localStorage | Key: `runs::{problemId}`, max 50 entries |
| `SubmissionStorage` | localStorage | Key: `submissions::{problemId}`, max 20 entries |
| `ExecutionService` | **API** | POSTs to `/api/execute` → `executor.ts` (UV/g++ via spawn) |

### Adding a production backend
Implement the interface, then export it from `services/index.ts` (typically behind an `env` check). The UI layer uses services only through the index — no changes needed there.

---

## Server vs. Client Boundary

| Context | What runs here |
|---|---|
| `+page.server.ts` | `courseLoader.ts`, `LocalCourseRepository` — Node.js `fs` |
| `onMount`, event handlers, components | All other services, Monaco editor |
| Either | `renderMarkdown.ts` (pure string → string, no Node APIs) |

Never import `courseParser.ts` or `courseLoader.ts` in a component or client-side file. Monaco must be imported inside `onMount` to avoid SSR crashes.

---

## Svelte 5 Runes Conventions

This codebase uses **Svelte 5 runes syntax throughout** — do not use the Svelte 4 `export let` / `$:` / `on:` API.

```svelte
<!-- Props -->
let { foo, bar = 'default' } = $props();

<!-- State -->
let count = $state(0);

<!-- Derived -->
let doubled = $derived(count * 2);

<!-- Side effects -->
$effect(() => { ... });

<!-- Snippets (replaces slots) -->
{#snippet mySnippet(arg)}...{/snippet}
{@render mySnippet(value)}
```

---

## CSS Rules

1. In `app.css`, the KaTeX `@import` **must appear before** any `@tailwind` directive. PostCSS processes rules in order; violating this breaks math rendering.
2. `postcss.config.cjs` uses CommonJS exports (not ESM) — this is intentional and correct even though `package.json` has `"type": "module"`.
3. Custom utility classes (`.btn`, `.badge`, `.tab-btn`, etc.) are defined at the bottom of `app.css` in a `@layer components` block.

---

## Monaco Editor Notes

- Loaded via **dynamic `import()` inside `onMount`** — never at module level.
- Uses a **no-op blob worker** (`new Worker(URL.createObjectURL(new Blob([...])))`). This is intentional: Monaco's Monarch tokenizer works without real workers; this avoids Vite worker bundling complexity.
- For a production build, replace the no-op worker with properly bundled Monaco workers.

---

## Running the Project

```bash
npm install
npm run dev          # Dev server at http://localhost:5173
npm run build        # Production build (adapter-node)
npm run preview      # Preview production build
npm run check        # svelte-check + tsc
```

**Environment variables:**
- `COURSES_DIR` — path to course content directory (default: `<cwd>/courses`)

---

## Authoring a New Course (Agent Workflow)

When asked to create a new course/track:

1. Create `courses/<track-slug>/course.yaml` with track metadata.
2. For each module, create `courses/<track-slug>/<NN>-<problem-slug>/` containing:
   - `module.yaml` (with `type: coding` or `type: reading`)
   - `problem.md` — for coding: clear problem statement, constraints, expected I/O. For reading: textbook-style content with KaTeX and Mermaid as needed; end with a "Recap" and a link to the next module.
   - `theory.md` — conceptual background, formulas, diagrams in Markdown/LaTeX
   - `tips.md` — incremental hints (avoid spoiling the solution) and a "Going deeper" section with markdown links to references
3. **Coding modules only:** add `starter/python.py` (and optionally `starter/cpp.cpp`), `solution/python.py`, `solution.md`, `requirements.txt` (if needed), and `expected_output/python.txt` (only when output is CPU-deterministic and easy to verify by hand — for GPU / model-load / network-dependent code, omit it; the platform returns a `pending` verdict).
4. **Reading modules only:** the four Markdown files are sufficient — no `starter/`, no `expected_output/`, no `requirements.txt`. The parser will ignore those directories if present.
5. No code changes required — the platform auto-discovers new content on next request.

A typical track mixes coding and reading modules: reading modules introduce the concepts and theory, coding modules let the user implement the ideas hands-on. The `protein-folding` track is the canonical example of this pattern (24 modules, ~half coding / half reading).

---

## Code Execution Architecture

Real code execution is handled server-side via a three-layer stack:

```
User clicks "Run"/"Submit"
  → ApiExecutionService (client, fetch)
    → POST /api/execute (+server.ts route)
      → executor.ts (Node.js child_process.spawn)
```

### executor.ts (`src/lib/server/executor.ts`)

**SERVER-SIDE ONLY.** Never import from client-side code or Svelte components.

Exports two functions:
- `runCode(language, code, requirementsPath?, timeoutMs?)` — run code, return stdout/stderr/timing
- `submitCode(language, code, expectedOutput, requirementsPath?, timeoutMs?)` — run + diff against expected

**Why `spawn` and not `exec`/`execSync`:**
- `spawn` does not invoke a shell (avoids shell injection surface)
- Non-blocking: does not stall the Node.js event loop while code runs
- Allows incremental stdout/stderr streaming
- Timeout via `SIGKILL` works reliably without waiting for a shell wrapper

**Python execution:**
- Code is written to a temp `.py` file (UUID name in `os.tmpdir()`)
- Without `requirements.txt`: `uv run python3 <tmpfile>`
- With `requirements.txt`: `uv run --python 3.11 -r <requirementsPath> python3 <tmpfile>`
- UV caches virtualenvs by requirements hash — subsequent runs with unchanged deps are fast
- Temp file is cleaned up in a `finally` block

**C++ execution:**
- Code written to a temp `.cpp` file
- Compiled: `g++ -O2 -o <tmpbin> <tmpcpp>`
- If compile fails (non-zero exit), stderr is returned immediately (no run step)
- Executed: `<tmpbin>`
- Both temp files cleaned up in `finally`

### UV Dependency Management (`requirements.txt`)

Each problem directory can optionally contain a `requirements.txt`:
```
courses/<track-slug>/<NN>-<problem-slug>/requirements.txt
```

This is a standard pip-compatible dependency file (e.g. `numpy\ntorch==2.3.0`). When present, the executor passes it to `uv run -r <path>`, which installs deps into a cached virtualenv before executing. UV's content-addressed caching means first run may be slow (installs deps) but subsequent runs are near-instant.

The `requirementsPath` field (absolute filesystem path) is stored on the `Problem` type and passed from the API route to the executor.

### Expected Output Grading (`expected_output/`)

Each problem directory can optionally contain pre-computed expected outputs:
```
courses/<track-slug>/<NN>-<problem-slug>/expected_output/python.txt
courses/<track-slug>/<NN>-<problem-slug>/expected_output/cpp.txt
```

Contents are the expected stdout (trimmed) for a correct solution. When present, the `submit` action in `/api/execute` diffs actual vs. expected output (after normalizing trailing whitespace per line). If absent, submit returns `verdict: 'pending'` with a message that no expected output is configured.

### API Route (`src/routes/api/execute/+server.ts`)

`POST /api/execute` — accepts `{ action, language, code, problemId }`.
- Resolves the problem via `loadProblem(trackSlug, problemSlug)` to get `requirementsPath` / `expectedOutput`
- Delegates to `runCode` or `submitCode` in `executor.ts`
- Returns `RunResult` or `SubmitResult` shapes (from `src/lib/types/execution.ts`)

### Client Service (`src/lib/services/local/executionService.local.ts`)

The previously mock-only `LocalExecutionService` has been replaced with `ApiExecutionService`, which POSTs to `/api/execute`. The `ExecutionService` interface and all call sites are unchanged.

---

## Planned / Future Extension Points

| Feature | Extension Point |
|---|---|
| Remote judge / sandbox | Replace `ApiExecutionService` with a call to Judge0 / Docker judge; executor.ts is already swappable |
| User accounts & progress | Implement `SubmissionStorage` / `RunHistoryStorage` against a backend API |
| Habit tracking | New service interface + UI route |
| Remote course source | Implement `CourseRepository` against an API or DB |
| Monaco workers | Replace no-op blob with proper Vite-bundled workers |
| Quiz modules | Extend `type` field beyond `reading | coding`; add a quiz renderer + answer-checking service |

---

## Updating This File

Update `agents.md` when:
- A new route is added or an existing route's purpose changes
- A new service interface or implementation is added
- The course content format (YAML schema, Markdown conventions) changes
- A significant new dependency is introduced
- The deployment target or build pipeline changes
- A new content type (quiz, reading-only, etc.) is implemented
