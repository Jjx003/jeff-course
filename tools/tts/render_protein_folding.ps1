$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
  uv run --python 3.11 build_course_narration_input.py `
    --course-dir ../../courses/protein-folding `
    --out ../../data/tts-input/protein-folding-gradual.json

  uv run --python 3.11 qwen_tts_pipeline.py render `
    --input ../../data/tts-input/protein-folding-gradual.json `
    --split-mode gradual `
    --voice voices/custom-reader.json `
    --out-dir ../../data/tts-output/protein-folding-gradual `
    --max-new-tokens 1536 `
    --batch-size 1 `
    --engine faster `
    --dtype auto `
    --device auto

  uv run --python 3.11 qwen_tts_pipeline.py align-manifest `
    --manifest ../../data/tts-output/protein-folding-gradual/manifest.json `
    --device auto
} finally {
  Pop-Location
}
