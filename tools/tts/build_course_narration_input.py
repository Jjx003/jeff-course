#!/usr/bin/env python3
"""Build a TTS input JSON from reading-module Markdown files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from qwen_tts_pipeline import TextItem, gradual_text_items, remove_repeated_titles


SECTION_FILES = [
    ("problem", "Overview", "problem.md"),
    ("theory", "Deep dive", "theory.md"),
    ("tips", "Further reading", "tips.md"),
]


def yaml_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
    return value


def module_type(module_dir: Path) -> str:
    module_yaml = module_dir / "module.yaml"
    if not module_yaml.exists():
        return "coding"
    return yaml_value(module_yaml.read_text(encoding="utf-8"), "type") or "coding"


def module_title(module_dir: Path) -> str:
    module_yaml = module_dir / "module.yaml"
    if not module_yaml.exists():
        return module_dir.name
    return yaml_value(module_yaml.read_text(encoding="utf-8"), "title") or module_dir.name


def normalize_id(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    return value.strip("-") or "item"


def build_items(course_dir: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for module_dir in sorted(path for path in course_dir.iterdir() if path.is_dir()):
        if module_type(module_dir) != "reading":
            continue

        title = module_title(module_dir)
        for section_id, section_label, filename in SECTION_FILES:
            path = module_dir / filename
            if not path.exists():
                continue
            markdown = path.read_text(encoding="utf-8").strip()
            if not markdown:
                continue

            source_id = normalize_id(f"{module_dir.name}-{section_id}")
            steps: list[TextItem] = remove_repeated_titles(gradual_text_items(markdown, source_id))
            for index, step in enumerate(steps, start=1):
                items.append(
                    {
                        "id": f"{source_id}-{index:03d}",
                        "title": f"{title} · {section_label} · {step.title}",
                        "text": step.text,
                    }
                )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    course_dir = Path(args.course_dir).resolve()
    items = build_items(course_dir)
    payload = {
        "title": f"{course_dir.name} gradual reading narration",
        "items": items,
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lengths = [len(item["text"]) for item in items]
    print(
        json.dumps(
            {
                "out": str(out),
                "items": len(items),
                "max_chars": max(lengths) if lengths else 0,
                "avg_chars": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
