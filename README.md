# Jeff Course

A local-first learning platform where courses are files, not products.

Jeff Course turns a folder of YAML, Markdown, quizzes, drills, and starter code
into a LeetCode-style course site. The goal is simple: if an agent can generate
good course material for a subject, you should be able to study it, improve it,
and share it with someone else.

![SvelteKit](https://img.shields.io/badge/SvelteKit-2-orange)
![Svelte](https://img.shields.io/badge/Svelte-5-orange)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Tailwind_CSS](https://img.shields.io/badge/Tailwind-3-38bdf8)
![DuckDB](https://img.shields.io/badge/DuckDB-local-yellow)

## What It Is

Jeff Course is a local web app for self-directed courses. It can host reading
modules, coding exercises, quizzes, tests, timed drills, progress tracking, and
study history. Course content lives in `courses/`. User progress lives in
`data/jeff-course.duckdb`.

It ships with tracks in machine learning, biology, systems, math, databases,
semiconductors, and poker theory, but the important part is the format: courses
are meant to be generated, edited, copied, and shared.

## Quick Start

```bash
git clone git@github-personal:Jjx003/jeff-course.git
cd jeff-course
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

For coding exercises, install the language tools you want to run:

- Python: install [`uv`](https://docs.astral.sh/uv/) so the app can run `uv run`.
- C++: install `g++` if you want to run C++ modules.
- Docker: optional, useful for isolated or heavier sandbox runs.

For Windows, macOS, Linux, tablets, phones, Chromebooks, and LAN access, see
[Setup Guide](docs/setup.md).

## Product Tour

| Browse courses | Work through coding exercises |
|---|---|
| <img src="docs/assets/screenshots/tracks-overview.png" alt="Track library showing available courses" width="560"> | <img src="docs/assets/screenshots/coding-workspace.png" alt="Coding exercise workspace with instructions, editor, and output" width="560"> |

| Read, review, and assess | Track steady progress |
|---|---|
| <img src="docs/assets/screenshots/reading-module.png" alt="Reading module with course explorer and article content" width="560"> | <img src="docs/assets/screenshots/progress-dashboard.png" alt="Stats dashboard with streak, points, time, and activity" width="560"> |

| Tests and quizzes |
|---|
| <img src="docs/assets/screenshots/test-module.png" alt="Test module introduction with pass threshold and question count" width="700"> |

## Why This Exists

Most learning platforms make the course the scarce thing. Jeff Course treats the
course as a portable artifact. An agent can draft a track on any topic, a human
can clean it up, and the result can be shared as ordinary files.

The platform is intentionally calm: local profiles, no feed, no marketplace
lock-in. It keeps progress, streaks, achievements, and practice history in the
local DuckDB file so a household or small study group can share one server
without turning study into noise.

## What You Can Build

Each course can mix several module types:

| Type | Use it for |
|---|---|
| Reading | Textbook-style lessons with Markdown, LaTeX, Mermaid diagrams, and focus mode |
| Coding | Python or C++ exercises with starter code, run/submit, and expected-output grading |
| Quiz | Self-checks with immediate feedback |
| Test | Exam-style assessments that reveal answers at the end |
| Drill | Timed generated practice for speed and fluency |
| Flashcards | Spaced-repetition decks that feed a cross-course review queue |

Any module type can be discussed with the built-in [AI tutor](#ai-tutor).

See [Course Authoring](docs/course-authoring.md) for the file format and sharing
workflow.

## Daily Review

Flashcard modules feed a single cross-course queue at `/review`. Every deck in
every track a learner is enrolled in contributes, and cards are scheduled per
learner with an SM-2-style algorithm: cards you grade *Again* come back in
minutes, cards you grade *Easy* drift weeks out.

The intent is that individual deck pages are where you meet a topic once, and
`/review` is where you keep it. A deck page still works on its own — it shows
what is due, what you have never seen, and offers a cram-the-whole-deck mode —
but the daily habit lives on the review page.

Scheduling state is per profile and lives in the local DuckDB file, alongside
an append-only review log. Resetting a deck clears its schedule without
removing the module's completion.

## AI Tutor

Every module page has a collapsed "Tutor" drawer on the right edge. It is a chat
with a coding/teaching model about the page you are on.

Rather than being handed a wall of context up front, the tutor looks things up
as it needs them. It can pull up the module's theory and tips, read the code
currently in your editor, and check the output of your last run or the grader's
verdict on your last submission — so on a coding module you can just ask "why
is this failing?" without pasting anything. The panel shows you which of these
it looked at while answering. Conversations are saved per learner and per
module, so a thread is still there when you come back.

The tutor is off unless you configure it. Copy `.env.example` to `.env` and set
an [OpenRouter](https://openrouter.ai/keys) key:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini
```

The key is only ever read by the server process. Reference solutions and quiz
answer keys are withheld from the model by default, so it hints instead of
handing over answers; set `TUTOR_ALLOW_SOLUTIONS=1` if you want it to see them.
Because `OPENROUTER_BASE_URL` accepts any OpenAI-compatible endpoint, you can
point the tutor at a model running on your own machine instead.

## Course Packs

Shared courses can also be installed as git-backed course packs. A pack repo may
contain either a `courses/` directory with one or more tracks, or a single track
with `course.yaml` at the repository root.

```bash
npm run course:add -- https://github.com/someone/ml-foundations-course-pack.git
npm run course:list
npm run course:update
npm run course:validate
```

The pack manifest lives at `data/course-packs.yaml` by default, and cloned repos
live under `data/course-packs/repos/`. Both are local user state. See
`course-packs.example.yaml` for the manifest shape.

## Local Profiles

On first launch, Jeff Course asks for the first learner profile. Anyone on the
trusted local network can add profiles from `/auth/users` or switch from the
profile picker. Each profile gets separate drafts,
completions, quiz/drill attempts, study time, achievements, run history, and
sandbox preferences while sharing the same course folders. Profiles enroll in
courses individually, so the main course screen stays focused on active study;
unenrolled courses remain available in the discovery catalog. Pausing a course
removes it from the active list without deleting progress, and resuming restores
the learner's existing work.

This is meant for trusted local-network sharing, such as a family computer or a
private home server. Profiles are not protected by passwords. It is not a public identity system; do not expose an
instance directly to the internet without a real network/auth boundary in front
of it.

## Project Layout

```text
jeff-course/
  courses/                 Course tracks, modules, Markdown, quizzes, drills
  data/                    Local DuckDB progress and generated/cache data
  docs/                    User-facing setup and authoring docs
  infra/docker/            Local sandbox Dockerfiles
  src/
    lib/content/           Server-side course loader and parser
    lib/server/            DuckDB, execution, grading, stats, sandbox sessions
    lib/services/          Client-facing service interfaces and implementations
    lib/components/        Svelte UI components
    routes/                SvelteKit pages and API routes
```

## Included Tracks

| Track | Modules |
|---|---:|
| Getting Hired at an AI Lab | 45 |
| Biochem & Org Chem Warm-up | 15 |
| Database Implementation in C++ | 17 |
| Immunology: From Recognition to Immune Engineering | 19 |
| Model Optimization Systems | 21 |
| Number Theory | 35 |
| Poker Theory: Mathematics & Strategy | 23 |
| Protein Folding and Design | 27 |
| Semiconductor Pipeline and Ecosystem | 19 |
| Supply Chain Systems | 12 |
| Introduction to Tensors | 11 |

## Scripts

```bash
npm run dev          # Start the dev server
npm run build        # Build with adapter-node
npm run preview      # Preview the production build
npm run check        # Svelte + TypeScript checks
npm run course:add -- <git-url>   # Install a git-backed course pack
npm run course:update             # Pull enabled course packs
npm run course:validate           # Validate built-in courses and enabled packs
```

## Environment Variables

Set these in the shell or in a git-ignored `.env` file at the repo root; see
`.env.example`.

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Enables the AI tutor. Unset means the tutor is disabled. |
| `OPENROUTER_MODEL` | Model the tutor uses. Defaults to `openai/gpt-4o-mini`. |
| `OPENROUTER_BASE_URL` | OpenAI-compatible endpoint for the tutor. Defaults to `https://openrouter.ai/api/v1`. |
| `TUTOR_ALLOW_SOLUTIONS=1` | Let the tutor read solutions and quiz answer keys. Off by default. |
| `COURSES_DIR` | Override the course content directory. Defaults to `<repo>/courses`. |
| `COURSE_PACKS_MANIFEST` | Override the course-pack manifest path. Defaults to `<repo>/data/course-packs.yaml`. |
| `COURSE_PACKS_DIR` | Override the course-pack checkout directory. Defaults to `<repo>/data/course-packs/repos`. |
| `DB_PATH` | Override the DuckDB file path. Defaults to `<repo>/data/jeff-course.duckdb`. |
| `TORCH_INDEX_URL` | Override the PyTorch wheel index used by Python exercises with `torch`. |
| `SANDBOX_SKIP_GPU_PROBE=1` | Skip Docker GPU probing on startup. |

## Tech Stack

SvelteKit 2, Svelte 5 runes, TypeScript, Tailwind CSS, Monaco Editor, unified
Markdown rendering, KaTeX, Mermaid, DuckDB, Vite 6, and adapter-node.

Important: `@sveltejs/vite-plugin-svelte` must stay on v5 or newer for Vite 6.

## Sharing Courses

A course is just a folder under `courses/<track-slug>/`. To share one, share that
folder. To install one, copy it into `courses/` or point `COURSES_DIR` at a
folder that contains one or more track directories.

For repeatable sharing, put that folder in a git repository and install it with
`npm run course:add -- <repo-url>`. Course-pack repos can be forked, pinned,
updated, and validated without changing app code.

The long-term spirit of the project is a commons of agent-generated courses:
small enough to fork, clear enough to review, and personal enough to study from.
