# Jeff Course TTS Pipeline

This is a standalone Qwen3-TTS pipeline for turning course text into audio assets.
It is intentionally separate from the SvelteKit app for now, but its input and
output manifests are stable enough for agents and future app routes to call.

Model source: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` on Hugging Face.

## Quick start

From the repository root:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py --help
```

Check the runtime before a long generation job:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py doctor
```

Generate one short file with the built-in English reader voice:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py render `
  --text "Machine learning models learn useful patterns from examples." `
  --voice voices/custom-reader.json `
  --out-dir ../../data/tts-output/smoke
```

Use the faster CUDA-graph engine for long course renders:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py render `
  --input ../../data/tts-input/protein-folding-gradual.json `
  --split-mode gradual `
  --voice voices/custom-reader.json `
  --out-dir ../../data/tts-output/protein-folding-gradual `
  --engine faster `
  --max-new-tokens 1536
```

`--engine stock` remains the default. `--engine faster` requires CUDA and uses
`faster-qwen3-tts` with Torch 2.6/CUDA wheels. It keeps the same manifest shape,
so `/api/audio/...` and word alignment continue to work.

Generate from an input JSON file:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py render `
  --input examples/course-snippet.json `
  --out-dir ../../data/tts-output/course-snippet
```

The first real generation will download the Qwen model weights. The 1.7B model
is large, so expect the first run to take a while.

Every render prints the selected runtime, for example
`Using cuda:0 (NVIDIA GeForce RTX 2070 SUPER); torch=2.4.1+cu124`, and stores
the same GPU details in `manifest.json`.

## Word-level alignment

After WAV generation, add word timestamps to an existing manifest with offline
wav2vec2 CTC forced alignment:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py align-manifest `
  --manifest ../../data/tts-output/protein-folding-gradual/manifest.json
```

The command uses `torchaudio`'s wav2vec2 ASR bundle, aligns each clip against
the exact `text` already stored in `manifest.json`, and writes clip-relative
timings as `words: [{ "text": "...", "startMs": 120, "endMs": 360,
"confidence": 0.92 }]`. It is resumable: clips with non-empty `words[]` are
skipped unless you pass `--force`. Use `--device cuda:0` to force GPU alignment
or `--bundle wav2vec2-large-960h` for the larger CTC model.

The manifest `text` field is the spoken text contract shared by generation,
fallback browser narration, and forced alignment. Markdown is normalized before
generation; tables are split into their own gradual step and converted to short
spoken prose instead of pipe-delimited Markdown. This is not a transcript
generator. Punctuation and unsupported symbols are ignored for alignment, while
the displayed word text is kept from the manifest. Numbers and math-heavy text
may align less precisely because the CTC model sees characters, not the TTS
model's spoken normalization.

## Course reading clips

For course pages, prefer `--split-mode gradual`. It mirrors focus-mode reading
steps and keeps each mini section as one audio clip:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py render `
  --input ../../courses/protein-folding/01-amino-acids/problem.md `
  --split-mode gradual `
  --voice voices/custom-reader.json `
  --out-dir ../../data/tts-output/protein-folding-01-amino-acids-gradual `
  --max-new-tokens 1536 `
  --engine faster
```

For the faster engine, clips are rendered one at a time because
`faster-qwen3-tts` exposes a single-text generation API. `--max-new-tokens 1536`
should fit most gradual steps; use `2048` for unusually long mini sections.

## Benchmarking Qwen vs. faster-qwen3-tts

Use `benchmark_qwen_tts.py` to compare stock `qwen-tts` and
[`faster-qwen3-tts`](https://github.com/andimarafioti/faster-qwen3-tts) on the
0.6B and 1.7B CustomVoice models with small course-style text inputs. It is a
standalone `uv run --script` tool so it can use `torch>=2.5.1`, which the
CUDA-graph implementation requires, without changing this pipeline's pinned
Torch 2.4 environment.

```powershell
uv run --script `
  --index-url https://download.pytorch.org/whl/cu124 `
  --extra-index-url https://pypi.org/simple `
  --index-strategy unsafe-best-match `
  tools/tts/benchmark_qwen_tts.py
```

For a quick smoke benchmark, reduce the work:

```powershell
uv run --script `
  --index-url https://download.pytorch.org/whl/cu124 `
  --extra-index-url https://pypi.org/simple `
  --index-strategy unsafe-best-match `
  tools/tts/benchmark_qwen_tts.py `
  --model-sizes 0.6B `
  --repeats 1 `
  --ttfa-repeats 1
```

Results are written to `data/tts-output/benchmarks/qwen-tts/` as WAV samples,
`benchmark-results.json`, and `benchmark-results.md`. RTF is audio duration
divided by generation time, so higher is better. TTFA is reported only for
`faster-qwen3-tts` streaming output because stock `qwen-tts` does not expose the
same streaming API here.

## Voice modes

- `custom`: uses Qwen's supported premium speakers. Good default for course
  reading. See `voices/custom-reader.json`.
- `clone`: uses the Base model with your own reference audio and transcript.
  Use only audio you own or have permission to clone. See `voices/clone-template.json`.
- `design`: uses the VoiceDesign model with a natural-language voice
  description. See `voices/design-template.json`.

The CustomVoice model supports these speakers at the time this tool was added:
`Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`,
and `Sohee`.

## Voice prompt caching

Qwen's Base voice-clone API exposes a reusable prompt object. Build it once:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py prepare-voice `
  --voice voices/clone-template.json `
  --out ../../data/tts-cache/my-voice.pkl
```

Then render with the cached prompt:

```powershell
uv run --directory tools/tts --python 3.11 qwen_tts_pipeline.py render `
  --input examples/course-snippet.json `
  --voice voices/clone-template.json `
  --voice-cache ../../data/tts-cache/my-voice.pkl `
  --out-dir ../../data/tts-output/my-voice-snippet
```

CustomVoice profiles such as `Aiden` do not expose a separate prompt object in
Qwen's public API. For those, the model is still loaded once per CLI run, and
the speaker is passed by name for each chunk. Stock `qwen-tts` can batch token
generation and then decode each generated audio-code sequence separately to
avoid a PyTorch/Transformers sliding-mask aliasing error on Windows. The faster
engine currently renders one clip per model call.

## Agent input format

Agents can pass either raw text/Markdown or JSON:

```json
{
  "title": "Intro to Gradients",
  "items": [
    {
      "id": "problem",
      "text": "A gradient tells us how a function changes as its input changes."
    },
    {
      "id": "recap",
      "text": "Recap: gradients point in the direction of steepest increase."
    }
  ]
}
```

Each item becomes one or more chunk WAV files plus a `manifest.json` with paths,
timings, generation parameters, and source metadata.

## Torch and GPU notes

The CLI defaults to `--device auto`, `--dtype auto`, and `--attn auto`.
On CUDA it prefers `bfloat16` only on Ampere-or-newer GPUs and uses `float16` on
older CUDA cards; otherwise it uses `float32`. Flash Attention is only selected
when explicitly requested with `--attn flash_attention_2`, because Windows
installs often work more reliably with PyTorch SDPA or eager attention.

This project mirrors the course executor's Torch install strategy: Python 3.11
plus the PyTorch CUDA wheel index when an NVIDIA GPU is present. The faster
engine needs `torch>=2.5.1`; the current lock uses Torch/Torchaudio 2.6 CUDA
wheels.

```powershell
uv sync --directory tools/tts --python 3.11 `
  --index-url https://download.pytorch.org/whl/cu124 `
  --extra-index-url https://pypi.org/simple `
  --index-strategy unsafe-best-match
```

If `doctor` still reports `cuda_available: false`, re-run the sync command
above or use the CUDA-enabled Docker fallback.

Qwen's package may also look for the SoX executable when handling audio. If
`doctor` shows `"sox": null`, install SoX and make sure `sox.exe` is on PATH
before doing voice cloning from reference audio.

If local Torch gets annoying, run the same CLI inside a Docker image with CUDA
support later. The input/output contract does not depend on the runtime.

Build and run the included CUDA-oriented image from `tools/tts`:

```powershell
docker build -t jeff-course-tts tools/tts
docker run --rm --gpus all `
  -v ${PWD}/data/tts-output:/out `
  -v ${PWD}/tools/tts/examples:/inputs `
  jeff-course-tts render --input /inputs/course-snippet.json --out-dir /out/course-snippet
```
