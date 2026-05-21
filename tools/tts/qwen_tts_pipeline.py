#!/usr/bin/env python3
"""Agent-friendly Qwen3-TTS input -> WAV output pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import re
import shutil
import sys
import time
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CUSTOM_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DEFAULT_CLONE_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
DEFAULT_DESIGN_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
GRADUAL_TARGET_CHARS = 760
GRADUAL_MAX_CHARS = 1180
GRADUAL_MIN_STANDALONE_CHARS = 140
ALIGNMENT_MODEL_CACHE: dict[tuple[str, str], tuple[Any, Any, list[str], dict[str, int]]] = {}


def add_windows_audio_tools_to_path() -> None:
    if os.name != "nt":
        return
    roots = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path(os.environ.get("ProgramFiles", "")),
        Path(os.environ.get("ProgramFiles(x86)", "")),
    ]
    dirs: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for exe_name in ("sox.exe", "ffmpeg.exe", "ffprobe.exe"):
            for exe in root.rglob(exe_name):
                dirs.append(str(exe.parent))
    if not dirs:
        return
    existing = os.environ.get("PATH", "")
    existing_parts = {part.lower() for part in existing.split(os.pathsep)}
    additions = [part for part in dict.fromkeys(dirs) if part.lower() not in existing_parts]
    if additions:
        os.environ["PATH"] = os.pathsep.join(additions + [existing])


add_windows_audio_tools_to_path()


@dataclass(frozen=True)
class TextItem:
    id: str
    text: str
    title: str | None = None


@dataclass(frozen=True)
class WordToken:
    text: str
    normalized: str


@dataclass(frozen=True)
class AlignmentPoint:
    token_index: int
    time_index: int
    score: float


@dataclass(frozen=True)
class CharacterSegment:
    char: str
    start_frame: int
    end_frame: int
    score: float


@dataclass(frozen=True)
class LoadedTTSModel:
    engine: str
    model: Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_voice(path: Path | None, args: argparse.Namespace) -> dict[str, Any]:
    voice: dict[str, Any] = {}
    if path is not None:
        voice.update(load_json(path))
    for key in (
        "mode",
        "model",
        "language",
        "speaker",
        "instruct",
        "ref_audio",
        "ref_text",
        "voice_cache",
    ):
        value = getattr(args, key, None)
        if value:
            voice[key] = value
    if getattr(args, "x_vector_only_mode", False):
        voice["x_vector_only_mode"] = True
    voice.setdefault("mode", "custom")
    voice.setdefault("language", "English")
    if voice["mode"] == "custom":
        voice.setdefault("model", DEFAULT_CUSTOM_MODEL)
        voice.setdefault("speaker", "Aiden")
    elif voice["mode"] == "clone":
        voice.setdefault("model", DEFAULT_CLONE_MODEL)
    elif voice["mode"] == "design":
        voice.setdefault("model", DEFAULT_DESIGN_MODEL)
    else:
        raise ValueError(f"Unsupported voice mode: {voice['mode']}")
    return voice


def strip_markdown(markdown: str) -> str:
    text = markdown_tables_to_spoken_text(markdown)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_markdown_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return len(cells) >= 2 and all(re.match(r"^:?-{3,}:?$", cell) for cell in cells)


def is_markdown_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def split_markdown_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_table_to_spoken_text(lines: list[str]) -> str:
    if len(lines) < 2 or not is_markdown_table_separator(lines[1]):
        return "\n".join(lines)

    headers = split_markdown_table_row(lines[0])
    spoken_rows: list[str] = []
    for line in lines[2:]:
        if not is_markdown_table_row(line):
            continue
        cells = split_markdown_table_row(line)
        parts: list[str] = []
        for index, cell in enumerate(cells):
            if not cell:
                continue
            header = headers[index] if index < len(headers) else ""
            parts.append(f"{header}: {cell}" if header else cell)
        if parts:
            spoken_rows.append("; ".join(parts))

    if not spoken_rows:
        return " ".join(headers)
    return "Table. " + ". ".join(spoken_rows) + "."


def markdown_tables_to_spoken_text(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    output: list[str] = []
    index = 0
    in_fence = False
    while index < len(lines):
        trimmed = lines[index].strip()
        if trimmed.startswith("```") or trimmed.startswith("~~~"):
            in_fence = not in_fence
            output.append(lines[index])
            index += 1
            continue
        if in_fence:
            output.append(lines[index])
            index += 1
            continue
        if (
            index + 1 < len(lines)
            and is_markdown_table_row(lines[index])
            and is_markdown_table_separator(lines[index + 1])
        ):
            table_lines = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and is_markdown_table_row(lines[index]):
                table_lines.append(lines[index])
                index += 1
            output.append(markdown_table_to_spoken_text(table_lines))
            continue
        output.append(lines[index])
        index += 1
    return "\n".join(output)


def is_markdown_heading(block: str) -> bool:
    return re.match(r"^#{1,4}\s+\S", block.strip()) is not None


def heading_text(block: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", block.strip())
    text = re.sub(r"\s+#+$", "", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text)
    return text.strip()


def markdown_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    in_math = False

    def flush() -> None:
        nonlocal current
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)
        current = []

    for line in markdown.replace("\r\n", "\n").split("\n"):
        trimmed = line.strip()
        starts_fence = trimmed.startswith("```") or trimmed.startswith("~~~")
        is_math_fence = trimmed == "$$"

        if not in_fence and not in_math and trimmed == "":
            flush()
            continue
        if not in_fence and not in_math and is_markdown_heading(trimmed):
            flush()
            blocks.append(trimmed)
            continue

        current.append(line)
        if starts_fence and not in_math:
            in_fence = not in_fence
        if is_math_fence and not in_fence:
            in_math = not in_math

    flush()
    return blocks


def is_thematic_break(block: str) -> bool:
    return re.match(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$", block.strip()) is not None


def has_rich_atomic_block(blocks: list[str]) -> bool:
    return any(block.strip().startswith(("```", "~~~", "$$")) or is_markdown_table_block(block) for block in blocks)


def is_markdown_table_block(block: str) -> bool:
    lines = [line for line in block.split("\n") if line.strip()]
    return len(lines) >= 2 and is_markdown_table_row(lines[0]) and is_markdown_table_separator(lines[1])


def split_long_list_block(block: str) -> list[str]:
    if len(block) <= GRADUAL_MAX_CHARS:
        return [block]

    chunks: list[str] = []
    current: list[str] = []

    def starts_top_level_list_item(line: str) -> bool:
        return re.match(r"^ {0,3}(?:[-*+]\s+|\d+[.)]\s+)", line) is not None

    def flush() -> None:
        nonlocal current
        chunk = "\n".join(current).strip()
        if chunk:
            chunks.append(chunk)
        current = []

    for line in block.split("\n"):
        if starts_top_level_list_item(line) and len("\n".join(current)) >= GRADUAL_TARGET_CHARS:
            flush()
        current.append(line)

    flush()
    return chunks if len(chunks) > 1 else [block]


def gradual_text_items(markdown: str, source_id: str) -> list[TextItem]:
    blocks = markdown_blocks(markdown)
    items: list[TextItem] = []
    pending: list[str] = []
    current_title = source_id
    current_length = 0
    should_speak_title = True

    def flush() -> None:
        nonlocal pending, current_length, should_speak_title
        content = "\n\n".join(pending).strip()
        if content:
            step = len(items) + 1
            body = strip_markdown(content)
            spoken = f"{current_title}. {body}" if should_speak_title else body
            items.append(TextItem(id=f"{source_id}-{step:03d}", title=current_title, text=spoken))
            should_speak_title = False
        pending = []
        current_length = 0

    for block in blocks:
        if is_thematic_break(block):
            continue
        if is_markdown_heading(block):
            if pending and (current_length >= GRADUAL_MIN_STANDALONE_CHARS or has_rich_atomic_block(pending)):
                flush()
            current_title = heading_text(block) or source_id
            should_speak_title = True
            continue
        if is_markdown_table_block(block):
            if pending:
                flush()
            pending.append(block)
            current_length = len(block)
            flush()
            continue
        for chunk in split_long_list_block(block):
            next_length = current_length + len(chunk)
            if pending and current_length >= GRADUAL_TARGET_CHARS and next_length > GRADUAL_MAX_CHARS:
                flush()
            pending.append(chunk)
            current_length += len(chunk)

    flush()

    for index in range(len(items) - 1, 0, -1):
        item = items[index]
        prev = items[index - 1]
        if len(item.text) >= GRADUAL_MIN_STANDALONE_CHARS:
            continue
        items[index - 1] = TextItem(
            id=prev.id,
            title=prev.title,
            text=f"{prev.text} {item.text}".strip(),
        )
        items.pop(index)

    return items


def remove_repeated_titles(items: list[TextItem]) -> list[TextItem]:
    cleaned: list[TextItem] = []
    last_title: str | None = None
    for item in items:
        text = item.text
        title = item.title or ""
        prefix = f"{title}. "
        if title == last_title and text.startswith(prefix):
            text = text[len(prefix) :]
        cleaned.append(TextItem(id=item.id, title=item.title, text=text))
        last_title = title
    return cleaned


def parse_input(args: argparse.Namespace) -> tuple[str | None, list[TextItem]]:
    if args.text:
        return None, [TextItem(id="text", text=args.text)]
    if not args.input:
        raise ValueError("Pass --text or --input")
    path = Path(args.input)
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        title = data.get("title") if isinstance(data, dict) else None
        items: list[TextItem] = []
        for index, item in enumerate(data.get("items", []), start=1):
            item_id = str(item.get("id") or f"item-{index:03d}")
            item_text = str(item.get("text") or "")
            item_title = item.get("title")
            if item_text.strip():
                items.append(TextItem(id=item_id, text=item_text, title=item_title))
        if not items and isinstance(data.get("text"), str):
            items.append(TextItem(id="text", text=data["text"], title=title))
        if not items:
            raise ValueError(f"No text items found in {path}")
        return title, items
    if args.split_mode == "gradual" and path.suffix.lower() in {".md", ".mdx"}:
        return path.stem, remove_repeated_titles(gradual_text_items(raw, path.stem))
    text = strip_markdown(raw) if args.markdown or path.suffix.lower() in {".md", ".mdx"} else raw.strip()
    return path.stem, [TextItem(id=path.stem, text=text)]


def chunk_text(text: str, max_chars: int) -> list[str]:
    text = strip_markdown(text)
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(sentence[i : i + max_chars].strip() for i in range(0, len(sentence), max_chars))
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return cleaned or "item"


def choose_device(device: str) -> str:
    if device != "auto":
        return device
    import torch

    return "cuda:0" if torch.cuda.is_available() else "cpu"


def choose_dtype(dtype: str, device: str) -> Any:
    import torch

    if dtype == "float32":
        return torch.float32
    if dtype == "float16":
        return torch.float16
    if dtype == "bfloat16":
        return torch.bfloat16
    if device.startswith("cuda"):
        if torch.cuda.is_available():
            idx = torch.cuda.current_device() if device == "cuda" else int(device.split(":")[-1])
            major, _minor = torch.cuda.get_device_capability(idx)
            if major >= 8 and torch.cuda.is_bf16_supported():
                return torch.bfloat16
        # Pre-Ampere cards can report BF16 availability through PyTorch even
        # when FP16 is the materially faster inference path.
        return torch.float16
    if hasattr(torch.backends, "mps") and device == "mps":
        return torch.float16
    return torch.float32


def load_model(model_id: str, device: str, dtype: Any, attn: str, engine: str = "stock", max_seq_len: int = 2048):
    if engine == "faster":
        if not device.startswith("cuda"):
            raise ValueError("faster-qwen3-tts requires a CUDA device")
        from faster_qwen3_tts import FasterQwen3TTS

        return LoadedTTSModel(
            engine=engine,
            model=FasterQwen3TTS.from_pretrained(
                model_id,
                device=device,
                dtype=dtype,
                attn_implementation="sdpa" if attn == "auto" else attn,
                max_seq_len=max_seq_len,
            ),
        )

    from qwen_tts import Qwen3TTSModel

    kwargs: dict[str, Any] = {"device_map": device, "dtype": dtype}
    if attn != "auto":
        kwargs["attn_implementation"] = attn
    return LoadedTTSModel(engine=engine, model=Qwen3TTSModel.from_pretrained(model_id, **kwargs))


def gpu_report(device: str) -> dict[str, Any]:
    import torch

    report: dict[str, Any] = {
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "selected_device": device,
    }
    if device.startswith("cuda") and torch.cuda.is_available():
        idx = torch.cuda.current_device() if device == "cuda" else int(device.split(":")[-1])
        report.update(
            {
                "cuda_device_name": torch.cuda.get_device_name(idx),
                "cuda_version": torch.version.cuda,
                "bf16_supported": torch.cuda.is_bf16_supported(),
                "memory_allocated_mb": round(torch.cuda.memory_allocated(idx) / 1024 / 1024, 1),
                "memory_reserved_mb": round(torch.cuda.memory_reserved(idx) / 1024 / 1024, 1),
            }
        )
    return report


def prompt_item_to_cpu(item: Any) -> Any:
    for attr in ("ref_code", "ref_spk_embedding"):
        value = getattr(item, attr, None)
        if hasattr(value, "detach"):
            setattr(item, attr, value.detach().cpu())
    return item


def load_voice_cache(path: str) -> Any:
    with Path(path).open("rb") as f:
        return pickle.load(f)


def save_voice_cache(path: Path, prompt_items: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(prompt_items, f)


def wav_duration_ms(path: Path) -> tuple[int | None, int | None]:
    try:
        with wave.open(str(path), "rb") as wav:
            sr = wav.getframerate()
            frames = wav.getnframes()
            return sr, round(frames / sr * 1000)
    except Exception:
        return None, None


def words_from_text(text: str, labels: set[str]) -> list[WordToken]:
    tokens: list[WordToken] = []
    for match in re.finditer(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?", text):
        original = match.group(0)
        normalized = original.upper().replace("’", "'")
        normalized = "".join(char for char in normalized if char in labels)
        if normalized:
            tokens.append(WordToken(text=original, normalized=normalized))
    return tokens


def build_alignment_trellis(emission: Any, tokens: Any, blank_id: int) -> Any:
    import torch

    frame_count = emission.size(0)
    token_count = tokens.size(0)
    trellis = torch.empty((frame_count + 1, token_count + 1), device=emission.device)
    trellis[0, 0] = 0
    trellis[0, 1:] = -float("inf")
    trellis[1:, 0] = torch.cumsum(emission[:, blank_id], dim=0)

    for time_index in range(frame_count):
        stay = trellis[time_index, 1:] + emission[time_index, blank_id]
        change = trellis[time_index, :-1] + emission[time_index, tokens]
        trellis[time_index + 1, 1:] = torch.maximum(stay, change)
    return trellis


def backtrack_alignment(trellis: Any, emission: Any, tokens: Any, blank_id: int) -> list[AlignmentPoint]:
    import torch

    token_count = tokens.size(0)
    time_index = int(torch.argmax(trellis[:, token_count]).item())
    path: list[AlignmentPoint] = []

    for token_index in range(token_count, 0, -1):
        while time_index > 0:
            stay = trellis[time_index - 1, token_index] + emission[time_index - 1, blank_id]
            change = trellis[time_index - 1, token_index - 1] + emission[time_index - 1, tokens[token_index - 1]]
            changed = bool(change > stay)
            probability = emission[time_index - 1, tokens[token_index - 1]].exp().item()
            path.append(AlignmentPoint(token_index - 1, time_index - 1, probability))
            time_index -= 1
            if changed:
                break
        if time_index == 0 and token_index > 1:
            raise ValueError("alignment backtrack reached the start before all transcript tokens")

    return list(reversed(path))


def merge_character_segments(path: list[AlignmentPoint], transcript: str) -> list[CharacterSegment]:
    segments: list[CharacterSegment] = []
    for char_index, char in enumerate(transcript):
        points = [point for point in path if point.token_index == char_index]
        if not points:
            continue
        segments.append(
            CharacterSegment(
                char=char,
                start_frame=points[0].time_index,
                end_frame=points[-1].time_index + 1,
                score=sum(point.score for point in points) / len(points),
            )
        )
    return segments


def align_words_with_wav2vec2(
    wav_path: Path,
    text: str,
    *,
    device: str,
    bundle_name: str,
) -> list[dict[str, Any]]:
    import torch
    import torchaudio

    bundles = {
        "wav2vec2-base-960h": torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H,
        "wav2vec2-large-960h": torchaudio.pipelines.WAV2VEC2_ASR_LARGE_960H,
    }
    if bundle_name not in bundles:
        raise ValueError(f"unsupported alignment bundle: {bundle_name}")

    runtime_device = choose_device(device)
    cache_key = (bundle_name, runtime_device)
    if cache_key in ALIGNMENT_MODEL_CACHE:
        bundle, model, labels, dictionary = ALIGNMENT_MODEL_CACHE[cache_key]
    else:
        bundle = bundles[bundle_name]
        labels = [label.upper() for label in bundle.get_labels()]
        dictionary = {label: index for index, label in enumerate(labels)}
        model = bundle.get_model().to(runtime_device).eval()
        ALIGNMENT_MODEL_CACHE[cache_key] = (bundle, model, labels, dictionary)

    separator = "|" if "|" in dictionary else " "
    blank_id = dictionary.get("-", 0)
    usable_labels = {label for label in dictionary if len(label) == 1 and label not in {separator, "-"}}

    word_tokens = words_from_text(text, usable_labels)
    if not word_tokens:
        return []

    transcript = separator.join(word.normalized for word in word_tokens)
    missing = sorted({char for char in transcript if char not in dictionary})
    if missing:
        raise ValueError(f"transcript contains labels not supported by {bundle_name}: {''.join(missing)}")

    waveform, sample_rate = torchaudio.load(str(wav_path))
    waveform = waveform.mean(dim=0, keepdim=True)
    if sample_rate != bundle.sample_rate:
        waveform = torchaudio.functional.resample(waveform, sample_rate, bundle.sample_rate)

    waveform = waveform.to(runtime_device)
    with torch.inference_mode():
        emissions, _ = model(waveform)
        emission = torch.log_softmax(emissions[0], dim=-1).cpu()

    token_ids = torch.tensor([dictionary[char] for char in transcript], dtype=torch.int64)
    if token_ids.numel() >= emission.size(0):
        raise ValueError(
            f"transcript is too dense for audio frames ({token_ids.numel()} labels, {emission.size(0)} frames)"
        )

    trellis = build_alignment_trellis(emission, token_ids, blank_id)
    path = backtrack_alignment(trellis, emission, token_ids, blank_id)
    char_segments = merge_character_segments(path, transcript)
    frame_ms = waveform.size(1) / bundle.sample_rate / emission.size(0) * 1000

    aligned: list[dict[str, Any]] = []
    char_cursor = 0
    for word in word_tokens:
        word_chars = [segment for segment in char_segments[char_cursor : char_cursor + len(word.normalized)]]
        char_cursor += len(word.normalized) + 1
        if not word_chars:
            continue
        start_ms = max(0, round(word_chars[0].start_frame * frame_ms))
        end_ms = max(start_ms + 1, round(word_chars[-1].end_frame * frame_ms))
        confidence = sum(segment.score for segment in word_chars) / len(word_chars)
        aligned.append(
            {
                "text": word.text,
                "startMs": start_ms,
                "endMs": end_ms,
                "confidence": round(float(confidence), 4),
            }
        )
    return aligned


def generation_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": not args.no_sample,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "temperature": args.temperature,
        "repetition_penalty": args.repetition_penalty,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def generate_custom_voice_decode_individually(
    model: Any,
    text: list[str],
    language: str,
    speaker: str,
    instruct: str,
    kwargs: dict[str, Any],
):
    texts = model._ensure_list(text)
    languages = [language] * len(texts)
    speakers = [speaker] * len(texts)
    instructs = [instruct] * len(texts)

    if model.model.tts_model_size in "0b6":
        instructs = [""] * len(texts)

    model._validate_languages(languages)
    model._validate_speakers(speakers)

    input_ids = model._tokenize_texts([model._build_assistant_text(t) for t in texts])
    instruct_ids = []
    for ins in instructs:
        if ins is None or ins == "":
            instruct_ids.append(None)
        else:
            instruct_ids.append(model._tokenize_texts([model._build_instruct_text(ins)])[0])

    gen_kwargs = model._merge_generate_kwargs(**kwargs)
    talker_codes_list, _ = model.model.generate(
        input_ids=input_ids,
        instruct_ids=instruct_ids,
        languages=languages,
        speakers=speakers,
        non_streaming_mode=True,
        **gen_kwargs,
    )

    wavs = []
    sample_rate = None
    for codes in talker_codes_list:
        decoded, fs = model.model.speech_tokenizer.decode([{"audio_codes": codes}])
        wavs.append(decoded[0])
        sample_rate = fs
    return wavs, sample_rate


def resolve_faster_speaker(model: Any, requested: str) -> str:
    supported = model.model.get_supported_speakers() or []
    if not supported:
        return requested
    for speaker in supported:
        if speaker == requested:
            return speaker
    for speaker in supported:
        if speaker.lower() == requested.lower():
            return speaker
    raise ValueError(f"Speaker {requested!r} is not supported by this model. Available: {', '.join(supported)}")


def synthesize_faster(runtime: LoadedTTSModel, voice: dict[str, Any], text: str | list[str], kwargs: dict[str, Any]):
    if isinstance(text, list):
        wavs: list[Any] = []
        sample_rate = None
        for one_text in text:
            one_wavs, sample_rate = synthesize_faster(runtime, voice, one_text, kwargs)
            wavs.extend(one_wavs)
        return wavs, sample_rate

    model = runtime.model
    mode = voice["mode"]
    language = voice.get("language", "English")
    if mode == "custom":
        return model.generate_custom_voice(
            text=text,
            language=language,
            speaker=resolve_faster_speaker(model, voice["speaker"]),
            instruct=voice.get("instruct", ""),
            **kwargs,
        )
    if mode == "design":
        return model.generate_voice_design(
            text=text,
            language=language,
            instruct=voice.get("instruct", ""),
            **kwargs,
        )
    if voice.get("voice_clone_prompt") is not None:
        return model.generate_voice_clone(
            text=text,
            language=language,
            voice_clone_prompt=voice["voice_clone_prompt"],
            xvec_only=bool(voice.get("x_vector_only_mode", False)),
            **kwargs,
        )
    return model.generate_voice_clone(
        text=text,
        language=language,
        ref_audio=voice["ref_audio"],
        ref_text=voice.get("ref_text"),
        xvec_only=bool(voice.get("x_vector_only_mode", False)),
        **kwargs,
    )


def synthesize(runtime: LoadedTTSModel, voice: dict[str, Any], text: str | list[str], kwargs: dict[str, Any]):
    if runtime.engine == "faster":
        return synthesize_faster(runtime, voice, text, kwargs)

    model = runtime.model
    mode = voice["mode"]
    language = voice.get("language", "English")
    text_count = len(text) if isinstance(text, list) else 1
    languages = [language] * text_count if isinstance(text, list) else language
    if mode == "custom":
        if isinstance(text, list) and len(text) > 1:
            return generate_custom_voice_decode_individually(
                model=model,
                text=text,
                language=language,
                speaker=voice["speaker"],
                instruct=voice.get("instruct", ""),
                kwargs=kwargs,
            )
        return model.generate_custom_voice(
            text=text,
            language=languages,
            speaker=[voice["speaker"]] * text_count if isinstance(text, list) else voice["speaker"],
            instruct=[voice.get("instruct", "")] * text_count if isinstance(text, list) else voice.get("instruct", ""),
            **kwargs,
        )
    if mode == "design":
        return model.generate_voice_design(
            text=text,
            language=languages,
            instruct=[voice.get("instruct", "")] * text_count if isinstance(text, list) else voice.get("instruct", ""),
            **kwargs,
        )
    if voice.get("voice_clone_prompt") is not None:
        return model.generate_voice_clone(
            text=text,
            language=languages,
            voice_clone_prompt=voice["voice_clone_prompt"],
            **kwargs,
        )
    return model.generate_voice_clone(
        text=text,
        language=languages,
        ref_audio=voice["ref_audio"],
        ref_text=voice.get("ref_text"),
        x_vector_only_mode=bool(voice.get("x_vector_only_mode", False)),
        **kwargs,
    )


def cmd_render(args: argparse.Namespace) -> int:
    import soundfile as sf

    title, items = parse_input(args)
    voice = load_voice(Path(args.voice) if args.voice else None, args)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    device = choose_device(args.device)
    dtype = choose_dtype(args.dtype, device)
    model = load_model(voice["model"], device, dtype, args.attn, args.engine, args.max_seq_len)
    if voice.get("voice_cache"):
        voice["voice_clone_prompt"] = load_voice_cache(voice["voice_cache"])
    gen_kwargs = generation_kwargs(args)
    runtime_gpu = gpu_report(device)
    print(f"Using {device} ({runtime_gpu.get('cuda_device_name', 'CPU')}); torch={runtime_gpu['torch']}", flush=True)

    manifest: dict[str, Any] = {
        "title": title,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "voice": {k: v for k, v in voice.items() if k != "voice_clone_prompt"},
        "runtime": {
            "device": device,
            "engine": args.engine,
            "dtype": str(dtype).replace("torch.", ""),
            "attn": args.attn,
            "gpu": runtime_gpu,
            "generation": gen_kwargs,
            "batch_size": args.batch_size,
        },
        "outputs": [],
    }

    pending: list[dict[str, Any]] = []
    for item in items:
        item_chunks = [item.text] if args.split_mode == "gradual" else chunk_text(item.text, args.max_chars)
        for chunk_index, chunk in enumerate(item_chunks, start=1):
            item_slug = slug(item.id)
            digest = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:10]
            wav_name = f"{item_slug}-{chunk_index:03d}-{digest}.wav"
            wav_path = out_dir / wav_name
            pending.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "path": wav_path,
                }
            )

    skipped = 0
    if args.skip_existing:
        remaining: list[dict[str, Any]] = []
        for entry in pending:
            wav_path = entry["path"]
            if wav_path.exists() and wav_path.stat().st_size > 44:
                sr, duration_ms = wav_duration_ms(wav_path)
                manifest["outputs"].append(
                    {
                        "id": entry["id"],
                        "title": entry["title"],
                        "chunk_index": entry["chunk_index"],
                        "sample_rate": sr,
                        "duration_ms_estimate": duration_ms,
                        "generation_ms": 0,
                        "batch_count": 0,
                        "skipped_existing": True,
                        "text": entry["text"],
                        "path": str(wav_path),
                    }
                )
                skipped += 1
            else:
                remaining.append(entry)
        pending = remaining
        if skipped:
            print(f"Skipping {skipped} existing clip(s).", flush=True)

    effective_batch_size = 1 if args.engine == "faster" else args.batch_size
    for start_index in range(0, len(pending), effective_batch_size):
        batch = pending[start_index : start_index + effective_batch_size]
        texts = [entry["text"] for entry in batch]
        start = time.perf_counter()
        try:
            wavs, sr = synthesize(model, voice, texts if len(texts) > 1 else texts[0], gen_kwargs)
            elapsed_ms = round((time.perf_counter() - start) * 1000)
        except Exception as exc:
            if len(batch) == 1:
                raise
            print(f"Batch of {len(batch)} failed ({exc}); falling back to single-chunk renders.", flush=True)
            for entry in batch:
                single_start = time.perf_counter()
                wavs, sr = synthesize(model, voice, entry["text"], gen_kwargs)
                elapsed_ms = round((time.perf_counter() - single_start) * 1000)
                wav = wavs[0]
                wav_path = entry["path"]
                sf.write(wav_path, wav, sr)
                manifest["outputs"].append(
                    {
                        "id": entry["id"],
                        "title": entry["title"],
                        "chunk_index": entry["chunk_index"],
                        "sample_rate": sr,
                        "duration_ms_estimate": round(len(wav) / sr * 1000),
                        "generation_ms": elapsed_ms,
                        "batch_count": 1,
                        "text": entry["text"],
                        "path": str(wav_path),
                    }
                )
                print(f"Wrote {wav_path} (batch fallback, {elapsed_ms} ms)", flush=True)
            continue
        for entry, wav in zip(batch, wavs):
            wav_path = entry["path"]
            sf.write(wav_path, wav, sr)
            manifest["outputs"].append(
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "chunk_index": entry["chunk_index"],
                    "sample_rate": sr,
                    "duration_ms_estimate": round(len(wav) / sr * 1000),
                    "generation_ms": elapsed_ms,
                    "batch_count": len(batch),
                    "text": entry["text"],
                    "path": str(wav_path),
                }
            )
            print(f"Wrote {wav_path} (batch {len(batch)}, {elapsed_ms} ms)", flush=True)

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    title, items = parse_input(args)
    voice = load_voice(Path(args.voice) if args.voice else None, args)
    chunks = len(items) if args.split_mode == "gradual" else sum(len(chunk_text(item.text, args.max_chars)) for item in items)
    print(json.dumps({"title": title, "items": len(items), "chunks": chunks, "voice": voice}, indent=2))
    return 0


def output_wav_path(manifest_path: Path, output: dict[str, Any]) -> Path | None:
    raw_path = output.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def cmd_align_manifest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest = load_json(manifest_path)
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list):
        raise ValueError(f"{manifest_path} does not contain an outputs array")

    aligned = 0
    skipped = 0
    failed = 0
    for index, output in enumerate(outputs, start=1):
        if not isinstance(output, dict):
            skipped += 1
            continue
        if not args.force and isinstance(output.get("words"), list) and output["words"]:
            skipped += 1
            continue

        text = output.get("text")
        wav_path = output_wav_path(manifest_path, output)
        if not isinstance(text, str) or not text.strip() or wav_path is None or not wav_path.exists():
            skipped += 1
            continue

        try:
            words = align_words_with_wav2vec2(
                wav_path,
                text,
                device=args.device,
                bundle_name=args.bundle,
            )
            output["words"] = words
            output["alignment"] = {
                "method": "wav2vec2-ctc-forced-alignment",
                "bundle": args.bundle,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            aligned += 1
            print(f"Aligned {output.get('id', index)} ({len(words)} words)", flush=True)
        except Exception as exc:
            failed += 1
            print(f"Failed {output.get('id', index)}: {exc}", file=sys.stderr, flush=True)
            if args.fail_fast:
                raise

    if not args.dry_run and aligned:
        tmp_path = manifest_path.with_suffix(f"{manifest_path.suffix}.tmp")
        tmp_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(manifest_path)

    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "aligned": aligned,
                "skipped": skipped,
                "failed": failed,
                "dry_run": bool(args.dry_run),
            },
            indent=2,
        )
    )
    return 1 if failed else 0


def cmd_prepare_voice(args: argparse.Namespace) -> int:
    voice = load_voice(Path(args.voice) if args.voice else None, args)
    if voice["mode"] != "clone":
        raise ValueError("prepare-voice currently applies to mode=clone voice profiles")
    if not voice.get("ref_audio"):
        raise ValueError("clone voice profiles need ref_audio")
    device = choose_device(args.device)
    dtype = choose_dtype(args.dtype, device)
    model = load_model(voice["model"], device, dtype, args.attn)
    runtime_gpu = gpu_report(device)
    print(f"Using {device} ({runtime_gpu.get('cuda_device_name', 'CPU')}); torch={runtime_gpu['torch']}", flush=True)
    prompt_items = model.model.create_voice_clone_prompt(
        ref_audio=voice["ref_audio"],
        ref_text=voice.get("ref_text"),
        x_vector_only_mode=bool(voice.get("x_vector_only_mode", False)),
    )
    save_voice_cache(Path(args.out).resolve(), [prompt_item_to_cpu(item) for item in prompt_items])
    print(f"Wrote voice cache {Path(args.out).resolve()}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    report: dict[str, Any] = {
        "python": sys.version,
        "executables": {
            "sox": shutil.which("sox"),
            "ffmpeg": shutil.which("ffmpeg"),
        },
        "imports": {},
    }
    try:
        import torch

        report["imports"]["torch"] = {
            "ok": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except Exception as exc:
        report["imports"]["torch"] = {"ok": False, "error": str(exc)}
    try:
        import soundfile

        report["imports"]["soundfile"] = {"ok": True, "version": soundfile.__version__}
    except Exception as exc:
        report["imports"]["soundfile"] = {"ok": False, "error": str(exc)}
    try:
        from qwen_tts import Qwen3TTSModel

        report["imports"]["qwen_tts"] = {"ok": True, "model_class": Qwen3TTSModel.__name__}
    except Exception as exc:
        report["imports"]["qwen_tts"] = {"ok": False, "error": str(exc)}
    print(json.dumps(report, indent=2))
    if args.strict:
        checks = [
            bool(report["executables"]["sox"]),
            report["imports"].get("torch", {}).get("ok"),
            report["imports"].get("qwen_tts", {}).get("ok"),
            report["imports"].get("soundfile", {}).get("ok"),
        ]
        return 0 if all(checks) else 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--input", help="Input .json, .txt, or .md file")
        p.add_argument("--text", help="Text to synthesize")
        p.add_argument("--markdown", action="store_true", help="Strip Markdown before narration")
        p.add_argument("--split-mode", choices=["chunk", "gradual"], default="chunk")
        p.add_argument("--voice", help="Voice profile JSON")
        p.add_argument("--mode", choices=["custom", "clone", "design"])
        p.add_argument("--model")
        p.add_argument("--language")
        p.add_argument("--speaker")
        p.add_argument("--instruct")
        p.add_argument("--ref-audio", dest="ref_audio")
        p.add_argument("--ref-text", dest="ref_text")
        p.add_argument("--voice-cache", dest="voice_cache", help="Pickled clone prompt cache from prepare-voice")
        p.add_argument("--x-vector-only-mode", action="store_true")
        p.add_argument("--max-chars", type=int, default=700)

    render = sub.add_parser("render", help="Generate WAV files and a manifest")
    add_common(render)
    render.add_argument("--out-dir", default="../../data/tts-output/latest")
    render.add_argument("--device", default=os.environ.get("QWEN_TTS_DEVICE", "auto"))
    render.add_argument("--engine", choices=["stock", "faster"], default=os.environ.get("QWEN_TTS_ENGINE", "stock"))
    render.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default="auto")
    render.add_argument("--attn", default=os.environ.get("QWEN_TTS_ATTN", "auto"))
    render.add_argument("--max-seq-len", type=int, default=2048, help="Static-cache context length for faster-qwen3-tts")
    render.add_argument("--max-new-tokens", type=int, default=2048)
    render.add_argument("--top-k", type=int, default=50)
    render.add_argument("--top-p", type=float, default=1.0)
    render.add_argument("--temperature", type=float, default=0.9)
    render.add_argument("--repetition-penalty", type=float, default=1.05)
    render.add_argument("--no-sample", action="store_true")
    render.add_argument("--batch-size", type=int, default=1, help="Chunks per model.generate call")
    render.add_argument("--skip-existing", action="store_true", help="Do not regenerate WAV files already present")
    render.set_defaults(func=cmd_render)

    validate = sub.add_parser("validate", help="Validate input and voice profile without loading Qwen")
    add_common(validate)
    validate.set_defaults(func=cmd_validate)

    align = sub.add_parser("align-manifest", help="Add word-level timestamps to an existing manifest")
    align.add_argument("--manifest", required=True, help="Path to data/tts-output/.../manifest.json")
    align.add_argument("--device", default=os.environ.get("TTS_ALIGN_DEVICE", "auto"))
    align.add_argument(
        "--bundle",
        choices=["wav2vec2-base-960h", "wav2vec2-large-960h"],
        default="wav2vec2-base-960h",
        help="Torchaudio wav2vec2 CTC bundle used for forced alignment",
    )
    align.add_argument("--force", action="store_true", help="Re-align clips that already have words[]")
    align.add_argument("--dry-run", action="store_true", help="Run alignment without writing manifest.json")
    align.add_argument("--fail-fast", action="store_true", help="Stop at the first clip alignment failure")
    align.set_defaults(func=cmd_align_manifest)

    prepare = sub.add_parser("prepare-voice", help="Cache a clone voice prompt for reuse")
    add_common(prepare)
    prepare.add_argument("--out", required=True, help="Output .pkl cache path")
    prepare.add_argument("--device", default=os.environ.get("QWEN_TTS_DEVICE", "auto"))
    prepare.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default="auto")
    prepare.add_argument("--attn", default=os.environ.get("QWEN_TTS_ATTN", "auto"))
    prepare.set_defaults(func=cmd_prepare_voice)

    doctor = sub.add_parser("doctor", help="Check Python, Torch, Qwen, and audio tooling")
    doctor.add_argument("--strict", action="store_true", help="Exit non-zero when required tools are missing")
    doctor.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
