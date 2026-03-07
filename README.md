# ML Course — Interactive Coding Exercises

A local-first web application for interactive machine-learning coding exercises.
Think LeetCode, but driven entirely by Markdown files on your filesystem —
no accounts, no cloud, no setup beyond `npm install`.

![SvelteKit](https://img.shields.io/badge/SvelteKit-2-orange)
![Svelte](https://img.shields.io/badge/Svelte-5-orange)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8)
![Monaco Editor](https://img.shields.io/badge/Monaco-Editor-0078d4)

---

## Features

- **Split-pane exercise UI** — instructional content left, Monaco editor right, draggable divider
- **Tabbed instructions** — Problem / Theory / Tips rendered from Markdown + LaTeX (KaTeX)
- **Python & C++ support** — language switcher with per-language draft persistence
- **Local persistence** — drafts, run history, and submissions saved in `localStorage`
- **Filesystem-driven content** — add a problem by adding a folder; zero app code changes
- **Mock execution** — Run/Submit flow with simulated output; clean interface for a real backend

---

## Quick Start

```bash
git clone git@github-personal:Jjx003/jeff-course.git
cd jeff-course
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Project Structure

```
jeff-course/
├── courses/                          # Course content — edit this to add problems
│   └── tensors/
│       ├── course.yaml               # Track metadata
│       ├── 01-intro-to-tensors/
│       │   ├── module.yaml           # Problem metadata
│       │   ├── problem.md            # Problem statement (Markdown + LaTeX)
│       │   ├── theory.md             # Theory explanation
│       │   ├── tips.md               # Tips & hints
│       │   └── starter/
│       │       ├── python.py         # Python starter code
│       │       └── cpp.cpp           # C++ starter code
│       ├── 02-matrix-multiplication/
│       └── 03-broadcasting/
└── src/
    ├── lib/
    │   ├── types/                    # Shared TypeScript types
    │   │   ├── course.ts             # Track, Problem, ProblemMeta, Language…
    │   │   └── execution.ts          # RunRequest, RunResult, Draft, snapshots…
    │   ├── content/                  # Server-side course parser (Node.js fs)
    │   │   ├── courseParser.ts       # Reads YAML + Markdown → app models
    │   │   └── courseLoader.ts       # Thin facade; resolves COURSES_DIR
    │   ├── markdown/
    │   │   └── renderMarkdown.ts     # unified → remark → rehype → KaTeX → HTML
    │   ├── services/                 # Interfaces + local implementations
    │   │   ├── courseRepository.ts
    │   │   ├── draftStorage.ts
    │   │   ├── runHistoryStorage.ts
    │   │   ├── submissionStorage.ts
    │   │   ├── executionService.ts
    │   │   └── local/                # localStorage + mock execution
    │   └── components/               # Svelte UI components
    │       ├── SplitPane.svelte
    │       ├── TabGroup.svelte
    │       ├── MarkdownRenderer.svelte
    │       ├── CodeEditor.svelte
    │       ├── LanguageSwitcher.svelte
    │       ├── OutputPanel.svelte
    │       ├── ProblemNav.svelte
    │       └── Header.svelte
    └── routes/
        ├── +page.svelte              # Landing page
        ├── tracks/+page.svelte       # Track list
        ├── tracks/[trackSlug]/       # Track detail
        └── tracks/[trackSlug]/problems/[problemSlug]/  # Exercise page
```

---

## Authoring Course Content

Add a new track or problem by creating files — no app code to edit.

### Track metadata — `courses/<track-slug>/course.yaml`

```yaml
title: "Introduction to Tensors"
slug: "tensors"
description: "Build tensor primitives from scratch."
tags: [machine-learning, linear-algebra]
difficulty: intermediate   # beginner | intermediate | advanced
order: 1
```

### Problem metadata — `courses/<track-slug>/<NN>-<problem-slug>/module.yaml`

```yaml
title: "Tensor Basics: Shape and Strides"
slug: "intro-to-tensors"
description: "Create a minimal Tensor class."
order: 1
difficulty: beginner
estimatedMinutes: 25
tags: [tensors, numpy]
languages: [python, cpp]
defaultLanguage: python
```

The `NN-` numeric prefix in the folder name controls problem ordering (lexicographic sort).

### Tab content

| File | Tab shown in UI |
|------|----------------|
| `problem.md` | Problem |
| `theory.md` | Theory |
| `tips.md` | Tips |

All files support standard Markdown, GitHub Flavored Markdown (tables, task lists),
and LaTeX math:

```markdown
Inline math: $C_{ij} = \sum_k A_{ik} B_{kj}$

Block math:
$$\text{stride}_i = \prod_{j=i+1}^{k-1} d_j$$
```

### Starter code

Place language-specific starter files in `starter/`:

```
starter/
  python.py
  cpp.cpp
```

---

## Architecture

The codebase is structured so local-only mode works end-to-end today,
and each layer can be swapped for a remote implementation later without
touching UI components.

```
┌─────────────────────────────────────────────────────────────┐
│  UI Components (Svelte)                                     │
│  know nothing about storage or execution internals          │
└────────────────────┬────────────────────────────────────────┘
                     │ calls
┌────────────────────▼────────────────────────────────────────┐
│  Service Interfaces                                         │
│  CourseRepository · DraftStorage · RunHistoryStorage        │
│  SubmissionStorage · ExecutionService                       │
└────────────────────┬────────────────────────────────────────┘
                     │ implemented by
┌────────────────────▼────────────────────────────────────────┐
│  Local Implementations (today)                              │
│  filesystem (server) · localStorage (client) · mock exec   │
├─────────────────────────────────────────────────────────────┤
│  Remote Implementations (future)                            │
│  HTTP API · cloud DB · sandboxed execution backend          │
└─────────────────────────────────────────────────────────────┘
```

### Extension points

| What to swap | How |
|---|---|
| Course content source | Implement `CourseRepository` to call a CMS/API instead of reading `courses/` |
| Override content directory | Set the `COURSES_DIR` environment variable |
| Persistence | Implement `DraftStorage` / `RunHistoryStorage` / `SubmissionStorage` to call a backend API |
| Code execution | Implement `ExecutionService` to call a sandboxed runner (Judge0, custom Docker, etc.) |
| Auth | Add an auth middleware in `+layout.server.ts`; services already have a clean boundary |

---

## Available Scripts

```bash
npm run dev          # Start dev server (http://localhost:5173)
npm run build        # Production build
npm run preview      # Preview production build locally
npm run check        # TypeScript + Svelte type check
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [SvelteKit 2](https://kit.svelte.dev) + [Svelte 5](https://svelte.dev) |
| Language | TypeScript 5 |
| Styling | [Tailwind CSS 3](https://tailwindcss.com) + `@tailwindcss/typography` |
| Editor | [Monaco Editor](https://microsoft.github.io/monaco-editor/) |
| Markdown + Math | `unified` · `remark-parse` · `remark-gfm` · `remark-math` · `rehype-katex` |
| YAML parsing | `js-yaml` |
| Course storage | Node.js `fs` (server-side load functions) |
| Client persistence | `localStorage` |
| Build tool | [Vite 6](https://vite.dev) |

---

## Supported Languages

| Language | Syntax highlighting | Starter code |
|---|---|---|
| Python | ✓ | ✓ |
| C++ | ✓ | ✓ |

Adding a new language: add its value to the `Language` union in `src/lib/types/course.ts`,
list it in `module.yaml`, and add a starter file in `starter/`.

---

## Included Tracks

### Tensors

Three problems that build intuition for the primitives behind every deep-learning framework:

| # | Problem | Topics |
|---|---|---|
| 1 | **Tensor Basics: Shape and Strides** | memory layout, C-contiguous strides, indexing |
| 2 | **Matrix Multiplication** | triple-loop matmul, cache-friendly loop ordering, FLOPs |
| 3 | **Broadcasting** | NumPy broadcasting rules, stride-trick implementation |
