# agents.md — Agent Onboarding Guide

> **Keep this file up to date.** If you make a significant structural change (new route, new service interface, new course content format, new dependency, new deployment target), update the relevant section before finishing your work.

---

## Project Purpose

**jeff-course** is a local-first, LeetCode-style platform for learning machine learning and deep learning through structured coding exercises and reading material. Course content lives in `courses/` as YAML + Markdown files (filesystem-driven); user progress (drafts, submissions, reading completions, achievements) lives in a single DuckDB file at `data/jeff-course.duckdb`.

The owner (Jeff) uses an agent to author new courses on demand: given a subject area, an agent writes the full course content (YAML metadata, Markdown explanations, starter code). The platform also includes a calm gamification layer (streaks, points, achievements, activity heatmap) on the `/stats` route to encourage consistent practice without turning learning into a dopamine treadmill.

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
│           ├── quiz.yaml        # quiz modules only: question definitions
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
    │   ├── server/                   # SERVER-SIDE ONLY
    │   │   ├── db.ts                  # DuckDB singleton + schema bootstrap
    │   │   ├── executor.ts            # Code execution (UV / g++ via spawn)
    │   │   ├── stats.ts               # Gamification engine (streaks, points, achievements)
    │   │   └── studyTime.ts           # Active-time aggregation helpers (heartbeat upsert + totals)
    │   ├── services/
    │   │   ├── courseRepository.ts    # interface
    │   │   ├── draftStorage.ts        # interface
    │   │   ├── runHistoryStorage.ts   # interface
    │   │   ├── submissionStorage.ts   # interface
    │   │   ├── executionService.ts    # interface
    │   │   ├── statsService.ts        # interface (gamification dashboard)
    │   │   ├── readingProgressService.ts  # interface (mark reading complete)
    │   │   ├── studyTimeService.ts    # interface (post study-time heartbeats)
    │   │   ├── index.ts               # service registry (dependency injection)
    │   │   ├── api/                   # DuckDB-backed implementations (fetch)
    │   │   │   ├── draftStorage.api.ts
    │   │   │   ├── runHistoryStorage.api.ts
    │   │   │   ├── submissionStorage.api.ts
    │   │   │   ├── statsService.api.ts
    │   │   │   ├── readingProgressService.api.ts
    │   │   │   └── studyTimeService.api.ts
    │   │   └── local/                 # filesystem / client-only implementations
    │   │       ├── courseRepository.local.ts
    │   │       └── executionService.local.ts  # POSTs to /api/execute (real execution)
    │   └── components/
    │       ├── Header.svelte
    │       ├── SplitPane.svelte
    │       ├── TabGroup.svelte
    │       ├── MarkdownRenderer.svelte
    │       ├── CodeEditor.svelte
    │       ├── LanguageSwitcher.svelte
    │       ├── OutputPanel.svelte
    │       ├── ProblemNav.svelte
    │       ├── ReadingView.svelte
    │       ├── ConfirmDialog.svelte       # reusable confirm/cancel modal
    │       ├── StudyTimeTracker.svelte    # gamification: invisible heartbeat + idle prompt
    │       ├── StreakBadge.svelte         # gamification: header pill
    │       ├── ProgressRing.svelte        # gamification: track progress
    │       ├── HeatmapCalendar.svelte     # gamification: yearly activity grid
    │       ├── AchievementCard.svelte     # gamification: locked/unlocked card
    │       ├── RewardToast.svelte         # gamification: non-intrusive notification
    │       ├── QuizView.svelte            # quiz module: intro → quiz → results phases
    │       └── InlineMarkdown.svelte      # tiny LaTeX/markdown renderer for option labels
    └── routes/
        ├── +layout.svelte
        ├── +page.svelte                                      # Landing page
        ├── stats/
        │   ├── +page.svelte                                  # Gamification dashboard
        │   └── +page.server.ts
        ├── sessions/                                          # Sandbox session dashboard
        │   ├── +page.svelte                                  # Live table + per-row drawer (SSE)
        │   └── +page.server.ts
        ├── tracks/
        │   ├── +page.svelte                                  # All tracks grid (+ per-track progress)
        │   ├── +page.server.ts
        │   └── [trackSlug]/
        │       ├── +page.svelte                              # Track detail + problem list with checkmarks
        │       ├── +page.server.ts
        │       └── problems/[problemSlug]/
        │               ├── +page.svelte                      # Main exercise (split pane)
        │               └── +page.server.ts
        └── api/
            ├── execute/+server.ts
            ├── drafts/[trackSlug]/[problemSlug]/[language]/+server.ts
            ├── runs/[trackSlug]/[problemSlug]/+server.ts
            ├── runs/[trackSlug]/[problemSlug]/[language]/+server.ts
            ├── submissions/[trackSlug]/[problemSlug]/+server.ts
            ├── stats/+server.ts                                       # GET aggregated stats
            ├── reading/[trackSlug]/[problemSlug]/+server.ts           # GET/POST reading completion
            ├── quiz/[trackSlug]/[problemSlug]/+server.ts              # GET aggregate quiz progress
            ├── quiz/[trackSlug]/[problemSlug]/attempt/+server.ts      # POST record one attempt
            └── study-time/heartbeat/+server.ts                        # POST active-time heartbeat
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
type: coding              # 'coding' | 'reading' | 'quiz'
languages: [python, cpp]  # CODING only — omit for reading/quiz modules
defaultLanguage: python   # CODING only — omit for reading/quiz modules
```

The `<NN>-` numeric prefix in the directory name controls sort order within a track. The `slug` field in `module.yaml` is what appears in the URL.

### Module types

`type: coding` (the default) is the original behaviour: an editor pane plus run/submit grading against optional `expected_output/`. The module folder must contain `starter/`, and may contain `requirements.txt` and `expected_output/` for grading.

`type: reading` is a textbook-style module: no editor, no run/submit, just `problem.md` + `theory.md` + `tips.md` rendered with KaTeX and Mermaid. Reading modules MUST omit `languages` and `defaultLanguage`. They MUST NOT have a `starter/` directory; if one exists the parser ignores it. Use reading modules for conceptual deep-dives between coding exercises.

`type: quiz` is an interactive self-assessment module: no editor, no runner. The module directory must contain a `quiz.yaml` file (see format below) alongside `problem.md` (used as the intro briefing on the pre-quiz screen). Quiz modules MUST omit `languages` and `defaultLanguage`.

Quiz UX flow (see `QuizView.svelte`):
1. **Intro phase** — meta header, `problem.md` briefing, stats card (question count, est. time, pass threshold, best score across all attempts), and a big "Start quiz" / "Retake quiz" CTA. Keyboard: <kbd>Enter</kbd> starts.
2. **Quiz phase** — one question at a time with a live score chip ("3 right · 1 wrong"), a question-type pill ("Multiple choice" / "True / False" / "Calculation"), the stem rendered with full markdown/LaTeX, and `InlineMarkdown`-rendered options (LaTeX works inside option text). Keyboard: <kbd>1</kbd>–<kbd>9</kbd> select MC options, <kbd>T</kbd>/<kbd>F</kbd> select true/false, <kbd>Enter</kbd>/<kbd>N</kbd> advance after answering.
3. **Results phase** — pass/fail hero with score bar + pass-threshold marker, best-score line, per-question review cards (filter All / Missed), retake + next-module CTAs. Keyboard: <kbd>R</kbd> retakes.

**Completion semantics:** a quiz is considered "completed" the first time the user scores **≥70%** (`QUIZ_PASS_THRESHOLD` in `src/lib/server/stats.ts`). On the first passing attempt the server inserts into `reading_completions` (same 5-pt reward, same streak credit, same achievement plumbing as readings) — there is no separate "Mark as complete" button; the threshold is the gate. Below-threshold attempts are still persisted to `quiz_attempts` so the intro screen can show "Best: X/Y · N attempts".

### Quiz (`quiz.yaml`)

Three question types are supported: `multiple_choice`, `true_false`, and `parametric`.

```yaml
# courses/<track-slug>/<NN>-<quiz-slug>/quiz.yaml
questions:
  - id: q1
    type: multiple_choice          # multiple_choice | true_false | parametric
    stem: "Question text ($LaTeX$ supported)"
    options: ["Option A", "Option B", "Option C", "Option D"]   # multiple_choice only
    correct: 1                     # 0-indexed for multiple_choice; boolean for true_false
    explanation: "Shown after answering. LaTeX supported."

  - id: q2
    type: true_false
    stem: "A higher pot odds percentage means you need less equity to call."
    correct: true
    explanation: "Correct. Pot odds % = call / (pot + call). A higher % means a worse price."

  - id: q_pot_odds
    type: parametric
    stem_template: "The pot is ${{pot}}. Villain bets ${{bet}}. What are your pot odds (your call ÷ total pot after calling)?"
    params:
      pot: { min: 60, max: 360, step: 30 }
      bet: { min: 20, max: 180, step: 20 }
    correct_formula: "Math.round(bet / (pot + 2 * bet) * 100)"
    distractor_formulas:
      - "Math.round(bet / (pot + bet) * 100)"
      - "Math.round(pot / (pot + 2 * bet) * 100)"
      - "Math.round((pot + bet) / (pot + 2 * bet) * 100)"
    answer_suffix: "%"
    explanation_template: >-
      You call ${{bet}} into a final pot of ${{pot + 2 * bet}}
      (${{pot}} + ${{bet}} bet + ${{bet}} call).
      Pot odds = {{bet}} / {{pot + 2 * bet}} = {{Math.round(bet/(pot+2*bet)*100)}}%.
```

#### Parametric question fields

| Field | Description |
|---|---|
| `stem_template` | Question text with `{{expr}}` interpolation slots (see below). |
| `params` | Map of param names to `{ min, max, step }`. Values are generated as multiples of `step` in `[min…max]`. |
| `correct_formula` | JS expression (param names in scope) yielding the correct numeric answer. |
| `distractor_formulas` | List of JS expressions yielding wrong-answer values (one per distractor). |
| `answer_suffix` | String appended to every option label, e.g. `"%"` or `" ms"`. |
| `explanation_template` | Explanation text with `{{expr}}` interpolation (same rules as stem_template). |

#### Template interpolation (`{{expr}}`)

Both `stem_template` and `explanation_template` support `{{expr}}` slots:

- **Plain variable** — `{{pot}}` → replaced with the current value of param `pot` (e.g. `120`).
- **JS expression** — `{{pot + 2 * bet}}` → evaluated with all param names in scope (e.g. `360`).

#### Param generation

For each `{ min, max, step }`, a random integer N in `[min/step … max/step]` is chosen and the final value is `N × step`. This guarantees "nice" multiples (e.g. multiples of 20 or 30) rather than arbitrary decimals.

#### Re-randomization on retake

"Retake quiz" calls `startNewAttempt()`, which re-runs `resolveQuestions()` and generates fresh random values for every parametric question. Static questions (`multiple_choice`, `true_false`) are unaffected — their options are re-normalized but not re-shuffled (they are not randomized to begin with).

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
| `DraftStorage` | **DuckDB** via `/api/drafts/...` | One row per `(problemId, language)`; upserted on save |
| `RunHistoryStorage` | **DuckDB** via `/api/runs/...` | One row per `(problemId, language)`; latest run only |
| `SubmissionStorage` | **DuckDB** via `/api/submissions/...` | Append-only; all submissions kept; the picker filters to accepted |
| `ExecutionService` | **API** | POSTs to `/api/execute` → `executor.ts` (UV/g++ via spawn) |
| `StatsService` | **DuckDB** via `/api/stats` | Computed from `submissions` + `reading_completions` + `study_sessions` + course content; achievements persisted on first unlock |
| `ReadingProgressService` | **DuckDB** via `/api/reading/...` | One row per reading module; first mark-complete preserved |
| `QuizService` | **DuckDB** via `/api/quiz/...` | One row per attempt; first passing attempt also flips `reading_completions` so a quiz pass grants 5 pts the same way a reading completion does |
| `StudyTimeService` | **DuckDB** via `/api/study-time/heartbeat` | Posts heartbeats with the running `active_ms` for the current session; server overwrites (never accumulates) |

### Persistence (DuckDB)

A single DuckDB file at `data/jeff-course.duckdb` is the source of truth for all persistent state. The handle is created once per process in `src/lib/server/db.ts` (cached on `globalThis` to survive Vite HMR). Tables:

- `drafts(problem_id, language, code, last_saved_at)` — PK on `(problem_id, language)`
- `runs(problem_id, language, id, code, result, timestamp)` — PK on `(problem_id, language)`
- `submissions(id, problem_id, language, code, result, timestamp)` — append-only
- `reading_completions(problem_id, completed_at)` — PK on `problem_id` (also used as the "quiz passed" flag — flipped by the first passing quiz attempt)
- `achievements(id, unlocked_at)` — PK on `id` (only unlocked rows are stored)
- `study_sessions(id, problem_id, started_at, active_ms, last_heartbeat_at)` — PK on `id` (one row per problem visit; upserted on every heartbeat)
- `quiz_attempts(id, problem_id, total, correct, passed, duration_ms, completed_at)` — append-only; one row per completed pass through a quiz

All tables are created via `CREATE TABLE IF NOT EXISTS` inside `dbReady`. There is no migration framework — for breaking schema changes, drop the file and restart.

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
   - `module.yaml` (with `type: coding`, `type: reading`, or `type: quiz`)
   - `problem.md` — for coding: clear problem statement, constraints, expected I/O. For reading: textbook-style content with KaTeX and Mermaid as needed; end with a "Recap" and a link to the next module. For quiz: brief intro/instructions for the question set.
   - `theory.md` — conceptual background, formulas, diagrams in Markdown/LaTeX
   - `tips.md` — incremental hints (avoid spoiling the solution) and a "Going deeper" section with markdown links to references
3. **Coding modules only:** add `starter/python.py` (and optionally `starter/cpp.cpp`), `solution/python.py`, `solution.md`, `requirements.txt` (if needed), and `expected_output/python.txt` (only when output is CPU-deterministic and easy to verify by hand — for GPU / model-load / network-dependent code, omit it; the platform returns a `pending` verdict).
4. **Reading modules only:** the four Markdown files are sufficient — no `starter/`, no `expected_output/`, no `requirements.txt`. The parser will ignore those directories if present.
5. **Quiz modules only:** add `quiz.yaml` with the question definitions (see Quiz format above). `problem.md` is used as intro/instructions. No `starter/`, no `expected_output/`, no `requirements.txt`.
5. No code changes required — the platform auto-discovers new content on next request.

A typical track mixes coding and reading modules: reading modules introduce the concepts and theory, coding modules let the user implement the ideas hands-on. The `protein-folding` track is the canonical example of this pattern (24 modules, ~half coding / half reading).

---

## Code Execution Architecture

Real code execution now flows through a **session-based sandbox pipeline**
(`src/lib/server/sandbox/`) that supports baremetal AND containerized
execution behind a single API. The legacy `executor.ts` is preserved for
reference; the new pipeline is the active path.

```
User clicks "Run"/"Submit"
  → apiSessionsService (client, fetch + EventSource SSE)
    → POST /api/sessions (returns sessionId immediately)
    → GET  /api/sessions/[id]/stream (SSE: stdout/stderr/status/exit)
      → sandbox/index.ts (orchestrator: queue, registry, persistence, grading)
        → sandbox/runtime/baremetal.ts  (uv/g++ via child_process — like old executor.ts)
        → sandbox/runtime/docker.ts     (docker run --rm with mounts + GPU passthrough)
```

### Sandbox module (`src/lib/server/sandbox/`)

| File | Responsibility |
|---|---|
| `types.ts` | `SessionRecord`, `SandboxMode`, `ResourceLimits`, status enums |
| `persistence.ts` | DuckDB CRUD against `sandbox_sessions` + `sandbox_preferences` |
| `registry.ts` | In-memory map of live sessions; fan-out for SSE log subscribers |
| `queue.ts` | Per-mode FIFO with bounded concurrency (env-tunable) |
| `runtime/baremetal.ts` | Streams uv/g++ child output via the registry |
| `runtime/docker.ts` | `docker run --rm` with cache mounts, GPU flags, label-based zombie reap |
| `runtime/detect.ts` | Cached host probe for Docker + NVIDIA Container Toolkit |
| `images.ts` | Lazy `docker build` from `infra/docker/*.Dockerfile` |
| `index.ts` | Public API: `startSession`, `subscribeToLogs`, `cancelSession`, etc |

Session modes:
- `baremetal` — current behavior, no isolation, no resource limits. Default.
- `docker` — sandboxed container, no GPU, `--network none`.
- `docker-gpu` — sandboxed container with `--gpus all` (NVIDIA Container Toolkit + WSL2 on Windows, or native on Linux).

### Cancellation semantics

The SSE stream is decoupled from the underlying child process: closing the
stream does NOT stop the spawn. The client must POST to
`/api/sessions/[id]/cancel` (which the page does in `beforeNavigate` and
`onDestroy`). Baremetal cancel is tree-kill (taskkill on Windows, process
group SIGKILL on POSIX). Docker cancel is `docker stop --time=2` then
`docker kill -s KILL` on the named container.

### Boot-time housekeeping

On the first import of `src/lib/server/sandbox/index.ts` (i.e. server boot)
we run two reapers in sequence:

1. `reapStaleSessionsOnBoot()` — any `sandbox_sessions` row still flagged
   `starting`/`running` is marked `crashed` so the UI doesn't show stale
   progress and the queue doesn't try to drain it.
2. `reapZombieContainers()` (in `runtime/docker.ts`) — `docker ps -a
   --filter label=jeff-course` followed by `docker rm -f` on every match.
   Soft-fails (5 s timeout, never throws) when docker isn't installed.

### UI surfaces

- `/sessions` — full dashboard. Live table of every session (most recent
  first), with per-row Cancel/Kill buttons and an expand drawer that
  subscribes to `/api/sessions/[id]/stream` to tail stdout/stderr. Polls
  `GET /api/sessions?limit=100` every 2 s and merges by id so an
  expanded drawer stays put across refreshes. Shows a capability banner
  at the top (Docker version + GPU device count, or a warning when
  Docker is missing). Bulk "Cancel all active" + "Refresh now" buttons
  in the toolbar.
- `SessionPill` (header) — small live pill showing `N running / M queued`
  when anything is active; hidden otherwise. Polls `?activeOnly=1` every
  2 s.
- Problem page — segmented control next to `LanguageSwitcher`
  (Baremetal / Container / Container + GPU) plus an Advanced panel with
  Memory / CPUs / Timeout / GPU device inputs. Disabled options carry a
  tooltip with the capability probe's failure reason. The picker seeds
  from `GET /api/sandbox/preferences/[trackSlug]` and pushes any change
  back via `PUT`.

### module.yaml `runtime:` (optional)

A coding module can suggest a default run mode + resources via:

```yaml
runtime:
  recommendedMode: docker-gpu     # baremetal | docker | docker-gpu
  resources:
    memoryMb: 8192
    cpus: 4
    timeoutMs: 600000
    gpu: all                       # 'all' | 'none' | { device: N }
```

The problem page falls back to this hint only when no per-track
preference is saved yet AND the recommended mode is actually available
on the host. Otherwise the user's saved preference (or baremetal) wins.

### DuckDB additions

- `sandbox_sessions(id PK, problem_id, language, action, mode, status,
  container_name, host_pid, started_at, completed_at, exit_code,
  error_message, resources_json, stdout_bytes, stderr_bytes,
  submit_verdict, submit_message, submit_score)` — one row per Run/Submit
  click. On boot any session still in `starting`/`running` is marked
  `crashed`.
- `sandbox_preferences(track_slug PK, preferred_mode, resources_json,
  updated_at)` — per-track sticky run-mode + resource limits.

### Legacy compat

`POST /api/execute` still works for backwards compatibility — internally
it starts a baremetal session, awaits completion via `collectOutput()`,
and folds the result back into the legacy `RunResult`/`SubmitResult`
shape. New code should call `services.sessionsService.start(...)`.

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

## Gamification Layer

The gamification system is intentionally calm: it surfaces progress and rewards consistency without becoming a slot machine. **Single source of truth: `src/lib/server/stats.ts`.** Everything else (the dashboard, the header pill, the toast, the track checkmarks) reads through `GET /api/stats` or one helper endpoint.

### Scoring

| Event | Points | Trigger |
|---|---|---|
| Solve a beginner coding problem (first time) | 10 | First accepted submission |
| Solve an intermediate coding problem (first time) | 20 | First accepted submission |
| Solve an advanced coding problem (first time) | 35 | First accepted submission |
| Complete a reading module (first time) | 5 | User clicks "Mark as complete" |
| Pass a quiz module (first time) | 5 | First attempt with score ≥ 70% — auto-credited, no manual button |
| Accumulate active study time | 0 | Per-tick heartbeat (5 s) — unlocks `hours-*` achievements only; no direct points |

Re-submitting an already-solved problem yields **no** additional points. This is by design — points reflect learning depth, not click frequency. Active study time deliberately grants **no** points — it would invite passive grinding. Instead it unlocks the four `hours-*` achievements (1h / 10h / 50h / 100h), which feel like quiet milestones rather than a meter you can game.

### Streaks

- An "active day" is any local-date with ≥ 1 first-solve OR ≥ 1 reading completion.
- Current streak counts consecutive active days ending today **or** yesterday (1-day grace so missing today doesn't immediately destroy the chain).
- Longest streak is computed over the full history.
- Dates use the server's local timezone (good enough for a single-user local app).

### Achievements

Seventeen achievements split across four categories (`milestone`, `consistency`, `depth`, `time`). The static list lives in `ACHIEVEMENT_DEFS` in `stats.ts`. Each achievement defines an ID, a title, a description, and a category; progress is evaluated against the user's current state on every `GET /api/stats`. When an achievement first unlocks, its ID + timestamp are persisted to the `achievements` table so the UI can show a stable "earned on" date. Locked achievements are not stored — they are re-evaluated from scratch each call.

Quiz-specific achievements: `quiz-pass` ("Quiz Conqueror" — pass your first quiz) and `quiz-perfect` ("Perfect Score" — get 100% on a quiz). Quizzes also count toward `theorist` ("Complete 5 readings or quizzes") alongside readings.

The four `time` achievements (`hours-1`, `hours-10`, `hours-50`, `hours-100`) read `totalActiveMs` from the study-time engine — see the "Time tracking" subsection below.

### UI surfaces

- `/stats` — full dashboard: five hero stats (streak, points, problems solved, **time invested**, achievements), year-long heatmap, per-track progress with rings, achievement grid (now including the four `hours-*` time achievements), personal highlights.
- Header — `StreakBadge` pill (`flame · streak · pts`); only visible once the user has any activity.
- `/tracks` — each track card shows a compact progress bar when in-progress.
- `/tracks/[slug]` — large progress ring + linear progress bar at the top; each problem row has a checkmark when completed.
- `/tracks/[slug]/problems/[slug]` — `RewardToast` appears on first-solve only; staggered achievement toasts follow if any unlocked. `StudyTimeTracker` runs invisibly behind the page and surfaces the "Are you still there?" prompt after 25 min of inactivity.
- Reading modules — "Mark as complete" CTA at the bottom of `ReadingView`; flips to a "Completed" card after the user clicks it.

### Adding a new achievement

1. Add an ID to the `AchievementId` union in `src/lib/types/gamification.ts`.
2. Append a definition to `ACHIEVEMENT_DEFS` in `src/lib/server/stats.ts`.
3. Add a branch to `evalAchievement(id, ctx)` returning `{ unlocked, progress, progressLabel }`.
4. (Optional) Add a glyph path to the `ICONS` map in `AchievementCard.svelte`.

No other code needs to change — the dashboard, toasts, and persistence pick it up automatically.

### Time tracking

The `study_sessions` table records active engagement per problem visit. `StudyTimeTracker.svelte` mounts on the problem page (keyed on `problemId`, so prev/next navigation ends the old session and starts a new one) and does the following:

- Generates a UUID `sessionId` on mount and posts an initial heartbeat with `activeMs = 0` so the row exists.
- Listens for `mousemove`, `keydown`, `scroll`, `click`, and `touchstart` on `window` (throttled to one update per 250 ms) to update an in-memory `lastActivityAt`.
- Every 5 s: if the tab is visible AND `Date.now() - lastActivityAt < 25 min`, adds 5 s to `activeMs`. Otherwise the timer is paused.
- Every 30 s: POSTs `{ sessionId, problemId, activeMs, startedAt }` to `/api/study-time/heartbeat`. The server **overwrites** `active_ms` rather than appending a delta — a lost or duplicated heartbeat can never double-count.
- On `visibilitychange → hidden`: flushes a heartbeat immediately so the server has the latest counter before the user might close the tab.
- On `pagehide` / component unmount: flushes via `navigator.sendBeacon` (with a `fetch keepalive` fallback) so the final counter survives unload.

**Idle threshold (25 min)** — after this much inactivity, the tracker pauses *and* opens a small "Are you still there?" prompt:
- **"Yes, I'm here"** → registers synthetic activity and resumes.
- **"Don't ask again"** → suppresses the prompt for the rest of this page load; the timer stays paused until real input arrives. This flag is **deliberately not persisted** — a fresh page load restores the safety net.

Server helpers live in `src/lib/server/studyTime.ts`:
- `upsertHeartbeat(sessionId, problemId, activeMs, startedAt)` — `INSERT … ON CONFLICT (id) DO UPDATE`.
- `getTotalActiveMs()` / `getActiveMsForDateKey(dateKey)` / `getActiveMsByDate()` — orphan-safe aggregates (sessions whose `problem_id` no longer maps to a current course module are excluded).

The aggregate is folded into `StatsSummary` as `totalActiveMs` + `activeMsToday`, surfaced in the "Time Invested" hero card on `/stats`, and feeds the four `hours-*` achievements.

### Design principles

- One subtle micro-animation per event (no confetti, no shake, no rotation).
- No countdowns, no FOMO copy, no leaderboards, no virtual currency.
- Streaks are forgiving (1-day grace) so a single off-day doesn't destroy motivation.
- Achievements are tied to learning behavior (persistence, breadth, depth, time) — never to clicks or grinding.
- Time-based progress is invisible by default: the tracker has no UI of its own and intentionally never says "30 min until your next badge".

---

## Planned / Future Extension Points

| Feature | Extension Point |
|---|---|
| Remote judge / sandbox | Replace `ApiExecutionService` with a call to Judge0 / Docker judge; executor.ts is already swappable |
| User accounts | Add an auth layer; partition every table on `user_id` |
| Remote course source | Implement `CourseRepository` against an API or DB |
| Monaco workers | Replace no-op blob with proper Vite-bundled workers |
| Quiz modules | **Implemented.** `type: quiz` in `module.yaml` + `quiz.yaml` questions file; `QuizView.svelte` renders the intro/quiz/results flow; attempts persisted in `quiz_attempts`; first ≥70% attempt flips `reading_completions` (5 pts + streak). |
| Streak freeze (skip-day token) | Extend `stats.ts` streak computation; store freezes in a new table |

---

## Updating This File

Update `agents.md` when:
- A new route is added or an existing route's purpose changes
- A new service interface or implementation is added
- The course content format (YAML schema, Markdown conventions) changes
- The DuckDB schema changes (new table, new column, new index)
- A new achievement is added or the scoring formula changes
- A significant new dependency is introduced
- The deployment target or build pipeline changes
- A new content type (quiz, reading-only, etc.) is implemented
