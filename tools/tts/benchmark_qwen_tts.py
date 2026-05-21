# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = [
#   "faster-qwen3-tts>=0.2.6",
#   "hf-xet>=1.2.0",
#   "numpy>=1.26",
#   "qwen-tts>=0.1.1",
#   "soundfile>=0.12",
#   "torch>=2.5.1,<2.7",
#   "torchaudio>=2.5.1,<2.7",
#   "transformers>=4.57",
# ]
# ///
"""Benchmark stock qwen-tts against faster-qwen3-tts on short CustomVoice inputs.

Run from the repository root. For CUDA wheels on Windows/NVIDIA, prefer:

uv run --script `
  --index-url https://download.pytorch.org/whl/cu124 `
  --extra-index-url https://pypi.org/simple `
  --index-strategy unsafe-best-match `
  tools/tts/benchmark_qwen_tts.py
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


DEFAULT_TEXTS = [
    "Machine learning models learn useful patterns from examples.",
    "A tensor stores numbers in a shape, and strides explain how those numbers sit in memory.",
    (
        "During training, we compute a loss, estimate how each parameter contributed to it, "
        "and then nudge the parameters in a better direction."
    ),
]


@dataclass
class RunMetric:
    engine: str
    model_size: str
    model_id: str
    text_id: str
    text_chars: int
    repeat: int
    generation_seconds: float
    audio_seconds: float
    rtf: float
    ttfa_ms: float | None
    sample_rate: int
    output_path: str


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return str(value)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def synchronize(device: str) -> None:
    if not device.startswith("cuda"):
        return
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
    except Exception:
        pass


def select_dtype(dtype_name: str):
    import torch

    if dtype_name == "float32":
        return torch.float32
    if dtype_name == "float16":
        return torch.float16
    if dtype_name == "bfloat16":
        return torch.bfloat16
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    if torch.cuda.is_available():
        return torch.float16
    return torch.float32


def runtime_report(device: str) -> dict[str, Any]:
    import torch

    report: dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "selected_device": device,
    }
    if torch.cuda.is_available():
        idx = 0 if device == "cuda" else int(device.split(":")[-1]) if device.startswith("cuda:") else 0
        report.update(
            {
                "cuda_device_name": torch.cuda.get_device_name(idx),
                "cuda_version": torch.version.cuda,
                "bf16_supported": torch.cuda.is_bf16_supported(),
            }
        )
    return report


def resolve_speaker(model: Any, requested: str) -> str:
    supported = model.get_supported_speakers() or []
    if not supported:
        return requested
    for speaker in supported:
        if speaker == requested:
            return speaker
    for speaker in supported:
        if speaker.lower() == requested.lower():
            return speaker
    available = ", ".join(supported)
    raise ValueError(f"speaker {requested!r} is not supported by this model; available: {available}")


def load_stock_model(model_id: str, device: str, dtype: Any, attn: str):
    from qwen_tts import Qwen3TTSModel

    kwargs: dict[str, Any] = {"device_map": device}
    if attn != "auto":
        kwargs["attn_implementation"] = attn
    try:
        return Qwen3TTSModel.from_pretrained(model_id, dtype=dtype, **kwargs)
    except TypeError:
        return Qwen3TTSModel.from_pretrained(model_id, torch_dtype=dtype, **kwargs)


def load_faster_model(model_id: str, device: str, dtype: Any, attn: str, max_seq_len: int, faster_repo: str | None):
    if faster_repo:
        repo_path = str(Path(faster_repo).resolve())
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
    from faster_qwen3_tts import FasterQwen3TTS

    return FasterQwen3TTS.from_pretrained(
        model_id,
        device=device,
        dtype=dtype,
        attn_implementation="sdpa" if attn == "auto" else attn,
        max_seq_len=max_seq_len,
    )


def gen_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "do_sample": not args.no_sample,
        "repetition_penalty": args.repetition_penalty,
    }


def save_audio(path: Path, audio: Any, sample_rate: int) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    array = np.asarray(audio, dtype=np.float32).reshape(-1)
    sf.write(path, array, sample_rate)
    return float(len(array) / sample_rate)


def benchmark_stock(
    model: Any,
    *,
    model_size: str,
    model_id: str,
    texts: list[str],
    speaker: str,
    language: str,
    instruct: str,
    args: argparse.Namespace,
    out_dir: Path,
) -> list[RunMetric]:
    metrics: list[RunMetric] = []
    kwargs = gen_kwargs(args)
    speaker = resolve_speaker(model, speaker)

    print(f"[stock {model_size}] warmup", flush=True)
    model.generate_custom_voice(
        text=texts[0][: args.warmup_chars],
        language=language,
        speaker=speaker,
        instruct=instruct,
        max_new_tokens=min(args.max_new_tokens, args.warmup_tokens),
    )

    for text_index, text in enumerate(texts, start=1):
        for repeat in range(1, args.repeats + 1):
            synchronize(args.device)
            start = time.perf_counter()
            wavs, sample_rate = model.generate_custom_voice(
                text=text,
                language=language,
                speaker=speaker,
                instruct=instruct,
                **kwargs,
            )
            synchronize(args.device)
            elapsed = time.perf_counter() - start
            output_path = out_dir / "stock" / model_size / f"text{text_index:02d}-run{repeat:02d}.wav"
            audio_seconds = save_audio(output_path, wavs[0], sample_rate)
            rtf = audio_seconds / elapsed if elapsed > 0 else 0.0
            print(f"[stock {model_size}] text {text_index} run {repeat}: {elapsed:.2f}s, {audio_seconds:.2f}s audio, RTF {rtf:.2f}", flush=True)
            metrics.append(
                RunMetric(
                    engine="stock-qwen-tts",
                    model_size=model_size,
                    model_id=model_id,
                    text_id=f"text{text_index:02d}",
                    text_chars=len(text),
                    repeat=repeat,
                    generation_seconds=elapsed,
                    audio_seconds=audio_seconds,
                    rtf=rtf,
                    ttfa_ms=None,
                    sample_rate=int(sample_rate),
                    output_path=str(output_path),
                )
            )
    return metrics


def measure_faster_ttfa(model: Any, text: str, speaker: str, language: str, instruct: str, args: argparse.Namespace) -> float:
    ttfas: list[float] = []
    kwargs = gen_kwargs(args)
    for _ in range(args.ttfa_repeats):
        synchronize(args.device)
        start = time.perf_counter()
        gen = model.generate_custom_voice_streaming(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
            chunk_size=args.chunk_size,
            **kwargs,
        )
        try:
            next(gen)
        finally:
            gen.close()
        synchronize(args.device)
        ttfas.append((time.perf_counter() - start) * 1000)
    return statistics.fmean(ttfas)


def benchmark_faster(
    model: Any,
    *,
    model_size: str,
    model_id: str,
    texts: list[str],
    speaker: str,
    language: str,
    instruct: str,
    args: argparse.Namespace,
    out_dir: Path,
) -> list[RunMetric]:
    metrics: list[RunMetric] = []
    kwargs = gen_kwargs(args)
    speaker = resolve_speaker(model.model, speaker)

    print(f"[faster {model_size}] warmup and CUDA graph capture", flush=True)
    model.generate_custom_voice(
        text=texts[0][: args.warmup_chars],
        language=language,
        speaker=speaker,
        instruct=instruct,
        max_new_tokens=min(args.max_new_tokens, args.warmup_tokens),
    )

    for text_index, text in enumerate(texts, start=1):
        ttfa_ms = measure_faster_ttfa(model, text, speaker, language, instruct, args) if args.ttfa_repeats else None
        for repeat in range(1, args.repeats + 1):
            synchronize(args.device)
            start = time.perf_counter()
            wavs, sample_rate = model.generate_custom_voice(
                text=text,
                language=language,
                speaker=speaker,
                instruct=instruct,
                **kwargs,
            )
            synchronize(args.device)
            elapsed = time.perf_counter() - start
            output_path = out_dir / "faster" / model_size / f"text{text_index:02d}-run{repeat:02d}.wav"
            audio_seconds = save_audio(output_path, wavs[0], sample_rate)
            rtf = audio_seconds / elapsed if elapsed > 0 else 0.0
            ttfa_text = f", TTFA {ttfa_ms:.0f}ms" if ttfa_ms is not None else ""
            print(f"[faster {model_size}] text {text_index} run {repeat}: {elapsed:.2f}s, {audio_seconds:.2f}s audio, RTF {rtf:.2f}{ttfa_text}", flush=True)
            metrics.append(
                RunMetric(
                    engine="faster-qwen3-tts",
                    model_size=model_size,
                    model_id=model_id,
                    text_id=f"text{text_index:02d}",
                    text_chars=len(text),
                    repeat=repeat,
                    generation_seconds=elapsed,
                    audio_seconds=audio_seconds,
                    rtf=rtf,
                    ttfa_ms=ttfa_ms,
                    sample_rate=int(sample_rate),
                    output_path=str(output_path),
                )
            )
    return metrics


def summarize(metrics: list[RunMetric]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[RunMetric]] = {}
    for metric in metrics:
        groups.setdefault((metric.engine, metric.model_size), []).append(metric)

    rows: list[dict[str, Any]] = []
    for (engine, model_size), group in sorted(groups.items()):
        generation = [m.generation_seconds for m in group]
        audio = [m.audio_seconds for m in group]
        rtf = [m.rtf for m in group]
        ttfa = [m.ttfa_ms for m in group if m.ttfa_ms is not None]
        rows.append(
            {
                "engine": engine,
                "model_size": model_size,
                "runs": len(group),
                "mean_generation_seconds": statistics.fmean(generation),
                "mean_audio_seconds": statistics.fmean(audio),
                "mean_rtf": statistics.fmean(rtf),
                "mean_ttfa_ms": statistics.fmean(ttfa) if ttfa else None,
            }
        )
    return rows


def write_markdown(report_path: Path, report: dict[str, Any]) -> None:
    rows = report["summary"]
    lines = [
        "# Qwen TTS Benchmark",
        "",
        f"Created: `{report['created_at']}`",
        "",
        "| Engine | Model | Runs | Mean gen s | Mean audio s | Mean RTF | Mean TTFA ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        ttfa = "" if row["mean_ttfa_ms"] is None else f"{row['mean_ttfa_ms']:.0f}"
        lines.append(
            "| {engine} | {model_size} | {runs} | {gen:.2f} | {aud:.2f} | {rtf:.2f} | {ttfa} |".format(
                engine=row["engine"],
                model_size=row["model_size"],
                runs=row["runs"],
                gen=row["mean_generation_seconds"],
                aud=row["mean_audio_seconds"],
                rtf=row["mean_rtf"],
                ttfa=ttfa,
            )
        )
    lines.extend(
        [
            "",
            "RTF is audio seconds divided by generation seconds, so higher is better.",
            "TTFA is measured only for faster-qwen3-tts streaming output; stock qwen-tts has no comparable streaming API here.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["both", "stock", "faster"], default="both")
    parser.add_argument("--model-sizes", nargs="+", default=["0.6B", "1.7B"], choices=["0.6B", "1.7B"])
    parser.add_argument("--model-kind", default="CustomVoice", choices=["CustomVoice"])
    parser.add_argument("--texts", nargs="*", default=DEFAULT_TEXTS)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--ttfa-repeats", type=int, default=3)
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--speaker", default="Aiden")
    parser.add_argument("--language", default="English")
    parser.add_argument("--instruct", default="Read as a calm, clear course narrator with precise diction.")
    parser.add_argument("--out-dir", default="data/tts-output/benchmarks/qwen-tts")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default="auto")
    parser.add_argument("--attn", default="auto")
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--warmup-tokens", type=int, default=32)
    parser.add_argument("--warmup-chars", type=int, default=80)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument("--no-sample", action="store_true")
    parser.add_argument("--faster-repo", help="Optional path to a faster-qwen3-tts checkout to import before site-packages.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    import torch

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false")

    dtype = select_dtype(args.dtype)
    report: dict[str, Any] = {
        "created_at": now_utc(),
        "args": vars(args),
        "runtime": runtime_report(args.device),
        "metrics": [],
        "summary": [],
    }

    all_metrics: list[RunMetric] = []
    for model_size in args.model_sizes:
        model_id = f"Qwen/Qwen3-TTS-12Hz-{model_size}-{args.model_kind}"
        if args.engine in {"both", "stock"}:
            print(f"Loading stock qwen-tts {model_id}", flush=True)
            load_start = time.perf_counter()
            stock_model = load_stock_model(model_id, args.device, dtype, args.attn)
            print(f"Loaded stock {model_size} in {time.perf_counter() - load_start:.1f}s", flush=True)
            all_metrics.extend(
                benchmark_stock(
                    stock_model,
                    model_size=model_size,
                    model_id=model_id,
                    texts=args.texts,
                    speaker=args.speaker,
                    language=args.language,
                    instruct=args.instruct,
                    args=args,
                    out_dir=out_dir,
                )
            )
            del stock_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        if args.engine in {"both", "faster"}:
            print(f"Loading faster-qwen3-tts {model_id}", flush=True)
            load_start = time.perf_counter()
            faster_model = load_faster_model(model_id, args.device, dtype, args.attn, args.max_seq_len, args.faster_repo)
            print(f"Loaded faster {model_size} in {time.perf_counter() - load_start:.1f}s", flush=True)
            all_metrics.extend(
                benchmark_faster(
                    faster_model,
                    model_size=model_size,
                    model_id=model_id,
                    texts=args.texts,
                    speaker=args.speaker,
                    language=args.language,
                    instruct=args.instruct,
                    args=args,
                    out_dir=out_dir,
                )
            )
            del faster_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    report["metrics"] = [asdict(metric) for metric in all_metrics]
    report["summary"] = summarize(all_metrics)
    json_path = out_dir / "benchmark-results.json"
    md_path = out_dir / "benchmark-results.md"
    json_path.write_text(json.dumps(report, indent=2, default=json_default), encoding="utf-8")
    write_markdown(md_path, report)
    print(f"Wrote {json_path}", flush=True)
    print(f"Wrote {md_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
