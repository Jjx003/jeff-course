# agents.md - Agent Onboarding Guide

> Keep this file current. If you change routes, services, persistence, course
> formats, execution, setup requirements, deployment assumptions, or major docs,
> update this guide before finishing.

## Project Purpose

`jeff-course` is a local-first course platform where courses are portable file
folders. It turns YAML, Markdown, starter code, quizzes, tests, and drills into
a browser-based learning app with progress tracking.

The philosophy matters:

- People should be able to learn any subject that an agent can generate course
  content for.
- Generated courses should be easy for humans to review, edit, copy, and share.
- The app should work for many device types: powerful workstations, ordinary
  laptops, low-power machines, and browser-only clients such as tablets.
- Progress and rewards should feel calm: useful streaks, achievements, and
  practice history, without feeds, accounts, leaderboards, or noisy incentives.

Course content lives in `courses/`. User progress and app state live in DuckDB
at `data/jeff-course.duckdb` by default.

Course content can also come from git-backed course packs. Enabled packs are
listed in `data/course-packs.yaml` and checked out under
`data/course-packs/repos/` by default. The app loads built-in courses first,
then enabled pack roots.

## User-Facing Docs

Keep these aligned with this file:

- `README.md` - front door: purpose, quick start, features, sharing model.
- `docs/setup.md` - platform/device setup, optional execution tools, Docker.
- `docs/course-authoring.md` - course file format and sharing workflow.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | SvelteKit 2 + Svelte 5 runes |
| Language | TypeScript strict mode |
| Styling | Tailwind CSS v3 + `@tailwindcss/typography` |
| Editor | Monaco Editor, loaded client-side in `onMount` |
| Markdown | unified, remark, rehype, KaTeX, Mermaid |
| Course parsing | `js-yaml` + Node `fs`, server-side only |
| Persistence | DuckDB native addon, server-side singleton |
| Execution | Session-based sandbox pipeline using `uv`, `g++`, and optional Docker |
| Deployment | `@sveltejs/adapter-node` |
| Build tool | Vite 6 |

Important: `@sveltejs/vite-plugin-svelte` must stay on v5 or newer for Vite 6.

## Cross-Platform Principles

Design changes and docs should assume different users have different devices.

- A normal desktop or laptop can run the Node server and use the app locally.
- Phones and tablets should be treated as browser clients. They can open a
  server running on another machine via `npm run dev -- --host 0.0.0.0`.
- Chromebooks and low-power devices may work through Linux development mode, but
  they are often better as browser clients.
- Reading, quiz, test, and drill modules should work without Python, C++, Docker,
  CUDA, or heavy local dependencies.
- Coding modules should degrade gracefully when optional tools are missing.
- Do not make Docker, CUDA, or a high-end GPU mandatory for general use.
- The app has passwordless local profiles for trusted LAN sharing. Do not expose
  shared or remote instances publicly without a stronger external access-control
  layer.

Optional execution tools:

| Tool | Needed for |
|---|---|
| `uv` | Python coding modules |
| `g++` | C++ coding modules |
| Docker | Containerized sandbox mode |
| NVIDIA driver + Docker GPU support | `docker-gpu` mode and heavy CUDA work |

Windows notes:

- PowerShell may block `npm.ps1`; use `npm.cmd run <script>` when needed.
- Use PowerShell syntax for env vars: `$env:COURSES_DIR = "C:\path\to\courses"`.
- Docker image build scripts require Git Bash or WSL when invoking `.sh` files.
- Baremetal cancellation uses `taskkill /F /T` for process trees.

POSIX notes:

- Bash-style env vars work: `COURSES_DIR=/path/to/courses npm run dev`.
- Baremetal cancellation uses process-group kill.

## Running And Verification

```bash
npm install
npm run dev
npm run build
npm run preview
npm run check
npm run course:add -- <git-url-or-local-path>
npm run course:update
npm run course:list
npm run course:validate
```

On Windows PowerShell, prefer this when script execution policy blocks npm:

```powershell
npm.cmd run check
```

If you only change Markdown docs, `npm.cmd run check` / `npm run check` is still
a useful sanity check, but note any pre-existing warnings separately.

Environment variables:

| Variable | Purpose |
|---|---|
| `COURSES_DIR` | Override course content root. Defaults to `<repo>/courses`. Multiple roots can be separated with the platform path delimiter. |
| `COURSE_PACKS_MANIFEST` | Override course-pack manifest path. Defaults to `<repo>/data/course-packs.yaml`. |
| `COURSE_PACKS_DIR` | Override course-pack checkout directory. Defaults to `<repo>/data/course-packs/repos`. |
| `DB_PATH` | Override DuckDB file path. Defaults to `<repo>/data/jeff-course.duckdb`. |
| `TORCH_INDEX_URL` | Override PyTorch wheel index for Python modules using `torch`. |
| `SANDBOX_SKIP_GPU_PROBE=1` | Skip Docker GPU probing at startup. |

## Directory Layout

```text
jeff-course/
  agents.md
  README.md
  docs/
    setup.md
    course-authoring.md
  courses/
    <track-slug>/
      course.yaml
      <NN>-<module-slug>/
        module.yaml
        problem.md
        theory.md
        tips.md
        solution.md          optional
        starter/             coding only
        solution/            optional coding reference code
        quiz.yaml            quiz/test only
        drill.yaml           drill only
        requirements.txt     optional coding deps
        expected_output/     optional deterministic grading refs
  static/
    courses/<track-slug>/    bundled course images
  data/
    jeff-course.duckdb       local progress DB
    cache/                   sandbox/Hugging Face caches
    course-packs.yaml        optional local course-pack manifest
    course-packs/repos/      default git checkout location for packs
  infra/docker/              local sandbox Dockerfiles
  tools/course-packs/        git-backed course pack manager CLI
  src/
    lib/content/             server-only course parser/loader
    lib/markdown/            Markdown, math, proof callout rendering
    lib/reading/             gradual reading splitting
    lib/server/              DuckDB, stats, grading, sandbox
    lib/services/            service interfaces and client implementations
    lib/components/          Svelte UI components
    routes/                  pages and API routes
```

## Course Content Format

Track metadata: `courses/<track-slug>/course.yaml`

```yaml
title: "Introduction to Tensors"
slug: "tensors"
description: "Build tensor primitives from scratch."
tags: [machine-learning, linear-algebra]
difficulty: intermediate
order: 1
```

Module metadata: `courses/<track-slug>/<NN>-<module-slug>/module.yaml`

```yaml
title: "Tensor Basics: Shape and Strides"
slug: "intro-to-tensors"
description: "Create a minimal Tensor class."
order: 1
difficulty: beginner
estimatedMinutes: 25
tags: [tensors, numpy]
type: coding
languages: [python, cpp]
defaultLanguage: python
```

Supported `type` values:

| Type | Required files | Notes |
|---|---|---|
| `reading` | `problem.md`, `theory.md`, `tips.md` | Full article plus focus mode. No editor. |
| `coding` | Markdown files plus `starter/` | Optional `solution/`, `solution.md`, `requirements.txt`, `expected_output/`. |
| `quiz` | `problem.md`, `quiz.yaml` | Immediate feedback. Passing attempt marks complete. |
| `test` | `problem.md`, `quiz.yaml` | Same schema as quiz, but answers/explanations wait until results. |
| `drill` | `problem.md`, `drill.yaml` | Timed numeric generated practice. |

Only coding modules should include `languages`, `defaultLanguage`, `starter/`,
`requirements.txt`, or `expected_output/`.

The numeric prefix in the directory name controls sorting. The URL uses the
`slug` field in `module.yaml`.

Markdown supports GitHub-flavored Markdown, inline/block LaTeX, Mermaid, and
proof-style callouts. Use `static/courses/<track-slug>/` for bundled images and
reference them as `/courses/<track-slug>/<image>.png`.

For more examples, see `docs/course-authoring.md`.

## Course Packs

A course pack is a git repo that contains either:

```text
courses/<track-slug>/course.yaml
```

or a single track at the repo root:

```text
course.yaml
01-module/module.yaml
```

Users and agents install packs with:

```bash
npm run course:add -- https://github.com/org/course-pack.git
```

This writes `data/course-packs.yaml` and clones the repo under
`data/course-packs/repos/<safe-pack-id>/`. `npm run course:update` fetches and
fast-forwards enabled git packs. `npm run course:validate` checks built-in
courses plus enabled packs for required files, unsupported module types,
duplicate slugs, missing starter files, and dependency-bearing coding modules.

Course-pack manifest shape:

```yaml
packs:
  - id: org/course-pack
    repo: https://github.com/org/course-pack.git
    ref: main
    enabled: true
    # Optional; defaults to courses/ when it exists, otherwise repo root.
    # coursesDir: courses
```

Bundled courses win track-slug collisions. Treat packs with coding modules,
`requirements.txt`, or starter code as trusted local code because exercises may
install dependencies and execute on the user's machine.

## Services And Boundaries

Server-only modules:

- `src/lib/content/courseParser.ts`
- `src/lib/content/courseLoader.ts`
- `src/lib/server/**`

Never import server-only modules into Svelte components or client-side service
files. Components should use data from load functions and services from
`src/lib/services/index.ts`.

Current services:

| Service | Implementation |
|---|---|
| Course repository | Server load functions use filesystem-backed local repository |
| Draft storage | API service backed by DuckDB |
| Run history | API service backed by DuckDB |
| Submission storage | API service backed by DuckDB |
| Reading progress | API service backed by DuckDB |
| Quiz progress | API service backed by DuckDB |
| Drill progress | API service backed by DuckDB |
| Study time | API service backed by DuckDB heartbeats |
| Stats | API service backed by server aggregate helpers |
| Sessions | API service with SSE output and DuckDB session records |
| Execution | Local client service that calls the session/execute APIs |

## Persistence

DuckDB is the single local source of truth. The default path is
`data/jeff-course.duckdb`; override with `DB_PATH`.

Main tables:

- `users`
- `auth_sessions`
- `drafts`
- `runs`
- `submissions`
- `reading_completions`
- `achievements`
- `study_sessions`
- `quiz_attempts`
- `drill_attempts`
- `sandbox_sessions`
- `sandbox_preferences`

Learner-owned tables include `user_id` so profiles have separate progress,
drafts, attempts, achievements, study time, sandbox sessions, and sandbox
preferences. Course files and enabled course packs remain shared by the server.

There is no migration framework. For breaking local schema changes during
development, stop the server and remove the DB file.

## Code Execution And Sandbox

Active execution flows through `src/lib/server/sandbox/`.

```text
Problem page
  -> sessions service
  -> POST /api/sessions
  -> GET /api/sessions/[id]/stream
  -> sandbox orchestrator
  -> baremetal or Docker runtime
```

Session modes:

| Mode | Behavior |
|---|---|
| `baremetal` | Spawns `uv` or `g++` directly on the host. Default. |
| `docker` | Runs in a short-lived local container with resource settings. |
| `docker-gpu` | Docker mode with NVIDIA GPU passthrough. |

`POST /api/execute` still exists as a legacy compatibility shim. New code should
prefer the session service.

Coding module grading:

- If `expected_output/<language>.txt` exists, submit compares stdout against it.
- If expected output is missing, submit returns a `pending` verdict.
- Omit expected output for nondeterministic, GPU-heavy, model-loading, or
  network-dependent exercises.

Optional module runtime hint:

```yaml
runtime:
  recommendedMode: docker-gpu
  resources:
    memoryMb: 8192
    cpus: 4
    timeoutMs: 600000
    gpu: all
```

The UI respects saved per-track preferences first. A module hint is only a
fallback when available on the host.

## Routes

Pages:

- `/` - landing page
- `/auth/setup` - first local learner profile setup
- `/auth/sign-in` - trusted-user profile picker and switching
- `/auth/users` - profile list and learner creation
- `/tracks` - all tracks
- `/tracks/[trackSlug]` - track detail
- `/tracks/[trackSlug]/problems/[problemSlug]` - reading/coding/quiz/test/drill page
- `/stats` - progress and gamification dashboard
- `/sessions` - sandbox session history and live logs

API routes include:

- `/auth/sign-out`
- `/api/sessions` and `/api/sessions/[id]/*`
- `/api/sandbox/capabilities`
- `/api/sandbox/preferences/[trackSlug]`
- `/api/execute`
- `/api/drafts/...`
- `/api/runs/...`
- `/api/submissions/...`
- `/api/stats`
- `/api/reading/...`
- `/api/quiz/...`
- `/api/drill/...`
- `/api/study-time/heartbeat`

## Svelte 5 Conventions

Use runes syntax:

```svelte
let { foo, bar = 'default' } = $props();
let count = $state(0);
let doubled = $derived(count * 2);

$effect(() => {
  // side effect
});
```

Do not use Svelte 4 `export let`, `$:`, or `on:` patterns in new code.

Monaco must stay dynamically imported inside `onMount`.

## CSS Rules

- In `src/app.css`, KaTeX `@import` must come before any `@tailwind` directive.
- `postcss.config.cjs` intentionally uses CommonJS despite `"type": "module"`.
- Shared component utilities live in `@layer components`.

## Gamification

The gamification layer is intentionally quiet and local.

- First accepted coding submission grants points based on difficulty.
- First reading completion grants 5 points.
- First passing quiz/test grants 5 points.
- First drill target clear marks the drill complete.
- Study time unlocks time achievements but does not grant points.
- Repeating solved modules does not farm points.

Core logic lives in `src/lib/server/stats.ts`. UI surfaces include `/stats`,
header streak/session pills, track progress, completion checkmarks, and toasts.

## Authoring New Courses

When asked to create a course:

1. Define the course spine first: audience, goals, prerequisites, module list,
   module types, shared vocabulary, figure needs, coding contracts, assessments.
2. Create `courses/<track-slug>/course.yaml`.
3. Create one folder per module with the correct files for its type.
4. Keep reading/quiz/drill modules usable on devices without local execution
   tools.
5. Add deterministic `expected_output/` only when grading is stable.
6. Put bundled figures under `static/courses/<track-slug>/`.
7. Run parser-facing checks and `npm run check` / `npm.cmd run check` when
   content or app code changes.
8. Update `README.md`, `docs/course-authoring.md`, or this file if the course
   format or workflow changes.

For large courses, use multi-agent authoring:

- Main agent owns the spine, `course.yaml`, shared terminology, and final pass.
- Writer agents get disjoint module ranges and must not edit outside them.
- Reviewer/integrator checks narrative flow, repeated definitions, broken paths,
  YAML shape, quiz validity, grading, and difficulty ramp.

## Update This File When

- A route is added, removed, or repurposed.
- A service interface or implementation changes.
- The course schema or Markdown conventions change.
- A DuckDB table, column, or index changes.
- Execution, sandboxing, Docker, GPU, or setup assumptions change.
- A new dependency or deployment target is introduced.
- The cross-platform user story changes.
- A major doc page is added or reorganized.
