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
- `docs/experience-plan.md` - product philosophy, experience priorities,
  quality gates, roadmap, ownership, and success measures.

Use `docs/experience-plan.md` for durable product decisions. New learner or
creator experiences should name the principle, priority, acceptance criterion,
and workstream they advance. Do not treat activity, time-on-site, points, or
content volume as success without outcome evidence.

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
| AI tutor | OpenRouter chat completions over `fetch`, with a hand-rolled tool-calling loop, streamed to the client as SSE |
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
| `OPENROUTER_API_KEY` | Enables the AI tutor. Absent means the tutor is disabled. |
| `OPENROUTER_MODEL` | Tutor model slug. Defaults to `openai/gpt-4o-mini`. |
| `OPENROUTER_BASE_URL` | OpenAI-compatible endpoint for the tutor. Defaults to `https://openrouter.ai/api/v1`. |
| `TUTOR_ALLOW_SOLUTIONS=1` | Allow the tutor to read solutions and quiz answer keys. Off by default. |

Tutor variables are read through `$env/dynamic/private`, not `process.env`,
because that is the only way a repo-root `.env` file reaches server code in this
setup. Everything else in the table is read from `process.env` directly. See
`.env.example`.

## Directory Layout

```text
jeff-course/
  agents.md
  README.md
  docs/
    setup.md
    course-authoring.md
    experience-plan.md
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
    lib/server/tutor/        OpenRouter client, agent loop, tools, context, conversations
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

Bundled courses win track-slug collisions. Treat every course pack as trusted
authored behavior, not only packs with coding modules. Markdown may render raw
HTML and external resources; parametric quiz and drill formulas are evaluated
as JavaScript expressions in the browser; coding modules and dependencies may
execute on the host or in containers. Structural validation does not establish
security, factual accuracy, or assessment validity. Review pack updates before
enabling them, especially when following a moving git ref.

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
| AI tutor | API service streaming reply text and tool activity over SSE, with DuckDB conversation records |

## Persistence

DuckDB is the single local source of truth. The default path is
`data/jeff-course.duckdb`; override with `DB_PATH`.

Main tables:

- `users`
- `auth_sessions`
- `course_enrollments`
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
- `tutor_messages`

Learner-owned tables include `user_id` so profiles have separate progress,
drafts, attempts, achievements, study time, sandbox sessions, and sandbox
preferences. Enrollment is also profile-scoped: `/tracks` shows enrolled courses
as the learner's active list and keeps other courses in a compact discovery
catalog. Course detail pages are syllabus previews, while module pages require
enrollment. Pausing a course keeps its `course_enrollments` row with
`enrolled_at = 0`, which preserves learner work and prevents startup progress
backfill from re-enrolling it; enrolling again replaces that marker with the
current timestamp. Course files and enabled course packs remain shared by the
server.

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

## AI Tutor

`TutorPanel.svelte` is a collapsed drawer rendered once per module page,
outside the module-type branch, so reading, coding, quiz, test, and drill pages
all get it.

The tutor is agentic: instead of stuffing the module material and the editor
buffer into every request, the system prompt is small and the model pulls what
it needs through tools. There is no LLM SDK. OpenRouter is OpenAI-compatible,
so tool calling is a `tools` array in the request plus `tool_calls` deltas in
the stream, and the loop is a plain `for` loop in `agent.ts`.

```text
TutorPanel
  -> tutorService
    -> POST /api/tutor/[trackSlug]/[problemSlug]/message
      -> buildTutorContext()   metadata + task statement only
      -> runAgent()            loop, max 4 steps
           -> streamChatCompletion()  one step; text or tool calls
           -> tools.ts                executes calls against disk + DuckDB
      -> tutor_messages        learner turn + reply + tool steps
```

Tools (`src/lib/server/tutor/tools.ts`):

| Tool | Reads |
|---|---|
| `read_learner_code` | the `drafts` row for this learner/module/language, line-numbered |
| `read_module_section` | `problem` / `theory` / `tips` markdown |
| `read_last_run` | latest `runs` row: stdout, stderr, status |
| `read_submission_result` | latest `submissions` row: verdict, score, failing diffs |

The last three are withheld on non-coding modules. The final loop step is sent
without tools, which forces a prose answer instead of an endless tool chain.

Rules to preserve:

- The API key stays server-side. `/api/tutor/config` exposes only `enabled` and
  the model slug.
- Tools resolve the learner and module from the session and the route, never
  from the request body. The client sends only the message, the open language,
  and the active tab. It cannot point the tutor at another learner's work.
- The editor buffer is read from the `drafts` table, not uploaded per message.
  The page passes a `flushDraft` callback so the pending autosave debounce is
  committed before a question is answered; without it the tutor reads code up
  to one debounce interval stale.
- `solution.md`, `solution/` code, and quiz answer keys are excluded unless
  `TUTOR_ALLOW_SOLUTIONS=1`, and no tool exposes them. The system prompt tells
  the model to hint first and escalate only when the learner stays stuck.
- Threads are scoped to `(user_id, problem_id)` and persist across reloads.
  Aborted replies are saved with whatever text and tool steps arrived.
- Tool activity streams to the client as `tool-start` / `tool-end` SSE events
  and is persisted in `tutor_messages.steps` as JSON, so reopening a thread
  still shows what the tutor looked at.
- A tool that throws must not kill the reply; the failure is passed back to the
  model as text and shown in the UI as a failed step.
- The tutor is optional. With no key configured, the drawer explains the setup
  and every other feature is unaffected. Do not make it a hard dependency.
- `tools/tutor-mock-openrouter.mjs` is a local stand-in endpoint for testing
  the pipeline without a key. It emits streamed tool calls on the first step of
  a turn and prose on the next, so it exercises the agent loop; pass
  `--no-tools` for prose only.

## Routes

Pages:

- `/` - landing page
- `/auth/setup` - first local learner profile setup
- `/auth/sign-in` - trusted-user profile picker and switching
- `/auth/users` - profile list and learner creation
- `/tracks` - enrolled courses plus the discovery catalog
- `/tracks/[trackSlug]` - course detail and enrollment preview
- `/tracks/[trackSlug]/problems/[problemSlug]` - reading/coding/quiz/test/drill page
- `/stats` - progress and gamification dashboard
- `/sessions` - sandbox session history and live logs

API routes include:

- `/auth/sign-out`
- `/api/sessions` and `/api/sessions/[id]/*`
- `/api/tutor/config`
- `/api/tutor/[trackSlug]/[problemSlug]` (GET thread, DELETE thread)
- `/api/tutor/[trackSlug]/[problemSlug]/message` (POST, SSE reply stream)
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
8. Follow the publication checklist and course-quality rubric in
   `docs/course-authoring.md` and `docs/experience-plan.md` for substantial or
   shared courses.
9. Update `README.md`, `docs/course-authoring.md`,
   `docs/experience-plan.md`, or this file if the course format, workflow, trust
   model, or major product assumptions change.

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
- Product principles, experience priorities, quality gates, ownership, or
  success measures change.
