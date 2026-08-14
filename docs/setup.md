# Setup Guide

This app runs as a local SvelteKit server. Any modern browser can use it, but one
computer needs to run the Node process.

## Requirements

Required for the web app:

- Node.js 20 or newer
- npm
- Git

Optional for coding modules:

- [`uv`](https://docs.astral.sh/uv/) for Python execution
- `g++` for C++ execution
- Docker Desktop or Docker Engine for containerized sandbox runs
- NVIDIA drivers and Docker GPU support for GPU-backed modules

Reading, quiz, test, and drill modules work without Python, C++, or Docker.

Optional for the AI tutor:

- An [OpenRouter](https://openrouter.ai/keys) API key, or any OpenAI-compatible
  endpoint you can reach from the machine running the server.

## Standard Local Setup

```bash
git clone git@github-personal:Jjx003/jeff-course.git
cd jeff-course
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

The app creates `data/jeff-course.duckdb` automatically the first time it needs
to save progress. On first launch, create the first learner profile. That first
profile inherits any pre-existing single-user progress in the database.

## Windows

Recommended:

1. Install Node.js 20+.
2. Install Git for Windows.
3. Install `uv` for Python exercises.
4. Install a C++ toolchain with `g++` if you want C++ exercises.
5. Optional: install Docker Desktop with WSL 2 integration for container mode.

PowerShell works fine:

```powershell
npm install
npm run dev
```

If `uv` or `g++` is installed but execution fails, open a new terminal and check:

```powershell
uv --version
g++ --version
```

## macOS

Install Node.js 20+ and Git. Homebrew is the easiest path for optional tools:

```bash
brew install uv gcc
npm install
npm run dev
```

Docker Desktop is optional. Use it if you want container isolation or expect to
run heavier dependency stacks.

## Linux

Install Node.js 20+, Git, and optional execution tools through your package
manager. Example for Debian/Ubuntu-style systems:

```bash
sudo apt update
sudo apt install git build-essential
npm install
npm run dev
```

Install `uv` separately for Python exercises. Docker Engine is optional.

## Tablets And Phones

Phones and tablets should be treated as browser clients. Run the app on a
desktop, laptop, or server, then open it from the mobile browser.

Start the dev server on your network:

```bash
npm run dev -- --host 0.0.0.0
```

Find the host computer's local IP address, then open:

```text
http://<host-ip>:5173
```

This is good for reading, quizzes, and review. Editing code on mobile works, but
it is not the best experience.

Each person should sign in with their own local profile so progress, drafts,
study time, achievements, and sandbox preferences stay separate.

## Chromebooks And Low-Power Devices

Best options:

- Use the device as a browser client connected to another computer running the app.
- If Linux development mode is available, install Node.js and run the standard setup.
- Keep coding execution in baremetal mode only if `uv` or `g++` are installed.

Large ML modules can be slow on low-power CPUs. Docker and GPU modes are meant
for machines that can comfortably run them.

## Remote Or Shared Machine

You can run Jeff Course on a machine on your LAN or a private server:

```bash
npm run dev -- --host 0.0.0.0
```

For production-style testing:

```bash
npm run build
npm run preview -- --host 0.0.0.0
```

Jeff Course has passwordless profile switching for trusted LAN sharing. It has
no public-account system, identity verification, rate limiting, or hardened
multi-tenant security. Do not expose it directly to the public internet unless you put it
behind your own access controls.

## AI Tutor

The tutor drawer on module pages is disabled until a key is configured. Copy
`.env.example` to `.env` at the repo root and fill in:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Shell variables work too, and take precedence over `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-... npm run dev
```

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
npm run dev
```

Notes:

- The key is only read by the server process. It is never sent to the browser,
  and the client only learns whether the tutor is enabled and which model is in
  use.
- Every learner profile on a shared instance uses the same key, so the machine's
  owner is paying for all of it. There is no per-profile spend limit.
- The tutor calls out to a third-party API, which is the one part of the app that
  is not local-first. Everything else keeps working with it disabled.
- `OPENROUTER_BASE_URL` accepts any OpenAI-compatible endpoint. To keep the
  tutor local, point it at something like `http://127.0.0.1:11434/v1` (Ollama)
  and set `OPENROUTER_API_KEY` to any non-empty placeholder. The model must
  support tool calling, or the tutor cannot read your code and will answer from
  the task statement alone.
- Conversations are stored in the `tutor_messages` table in the local DuckDB
  file. Clearing a thread in the UI deletes those rows.
- The tutor answers by looking things up: module theory and tips, the code in
  your editor, your last run's output, and the grader's last verdict. Those
  lookups happen on the server against your own saved work, and the panel lists
  which ones ran. Nothing is read unless you ask a question.

To develop against the tutor without spending tokens, run the bundled mock
endpoint in a second terminal:

```bash
node tools/tutor-mock-openrouter.mjs 8799
OPENROUTER_API_KEY=test OPENROUTER_BASE_URL=http://127.0.0.1:8799/v1 npm run dev
```

The mock answers the first step of each turn with streamed tool calls and the
next with prose, so it exercises the whole agent loop. Pass `--no-tools` to get
plain replies instead.

## Docker Sandbox

Docker is optional. The app can run code directly on the host in baremetal mode.
When Docker mode is selected, the app builds local images from `infra/docker/`
as needed.

You can also build them manually:

```bash
bash infra/docker/build.sh
```

On Windows, run that command from Git Bash or WSL. Docker GPU mode requires an
NVIDIA GPU, working host drivers, and Docker GPU passthrough.

## Common Fixes

If courses do not show up, confirm the content directory:

```bash
COURSES_DIR=/path/to/courses npm run dev
```

On Windows PowerShell:

```powershell
$env:COURSES_DIR = "C:\path\to\courses"
npm run dev
```

If progress needs to be reset, stop the server and remove the DuckDB file:

```bash
rm data/jeff-course.duckdb
```

On Windows PowerShell:

```powershell
Remove-Item data\jeff-course.duckdb
```

If Vite or Svelte errors after dependency updates, check that
`@sveltejs/vite-plugin-svelte` is v5 or newer.
