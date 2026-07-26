#!/usr/bin/env python3
"""Validate a student-facing classroom material JSON record (worksheet,
homework sheet, or learning game) for structural completeness, then
optionally render it to Markdown.

This checks STRUCTURE only -- it does not judge whether the tasks/questions
are pedagogically good, factually correct, or age-appropriate; that stays a
human/agent authoring decision. Unlike CV5512 lesson plans, these 3 material
types have very little hard regulatory structure -- most of what's checked
here is basic shipping-safety (does every homework item have an answer? does
every item have a task?), not a legally-mandated format. Stdlib only, local,
deterministic -- no AI/network of any kind.

Errors block (exit 1); warnings are quality signals worth acting on but
don't block (exit 0 with warnings printed).

Usage:
    python validate_material.py material.json [--render material.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_MATERIAL_TYPES = {"worksheet", "homework", "game"}


def item_label(item: dict, index: int) -> str:
    item_id = item.get("id") if isinstance(item, dict) else None
    return f"items[{index}] (id={item_id!r})" if item_id else f"items[{index}]"


def validate(material: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("material_type", "subject", "grade", "topic", "items"):
        if field not in material:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    material_type = material["material_type"]
    if material_type not in VALID_MATERIAL_TYPES:
        errors.append(f"material_type must be one of {sorted(VALID_MATERIAL_TYPES)}, got {material_type!r}")
        return errors, warnings

    for field in ("subject", "grade", "topic"):
        if not str(material.get(field, "")).strip():
            errors.append(f"{field} must be a non-empty string")

    items = material.get("items")
    if not isinstance(items, list) or len(items) == 0:
        errors.append("items must be a non-empty list")
        items = []

    for i, item in enumerate(items):
        label = item_label(item, i) if isinstance(item, dict) else f"items[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue

        if not str(item.get("task", "")).strip():
            errors.append(f"{label}: task is required and must be non-empty")

        if material_type == "worksheet":
            if not str(item.get("response_space", "")).strip():
                warnings.append(f"{label}: missing response_space -- students need a described blank/table/diagram to fill in at their desk, not just a question")

        elif material_type == "homework":
            if not str(item.get("answer", "")).strip():
                errors.append(f"{label}: answer is required and must be non-empty -- a homework item shipped to students must be covered by the answer key, no gaps")
            if not str(item.get("difficulty", "")).strip():
                warnings.append(f"{label}: missing difficulty -- homework items are conventionally grouped/tagged by difficulty (co_ban/van_dung/nang_cao) or type")

    if material_type == "game":
        rules = str(material.get("rules", "")).strip()
        if not rules:
            errors.append("rules is required for material_type=game and must be non-empty (setup through win condition)")
        else:
            topic = str(material.get("topic", "")).strip()
            if topic and topic.lower() not in rules.lower():
                warnings.append(f"rules text does not mention the declared topic {topic!r} -- verify the game actually ties back to this lesson's content, not a generic activity")

        duration = material.get("estimated_duration_minutes")
        if not isinstance(duration, int) or duration <= 0:
            warnings.append("estimated_duration_minutes is missing or not a positive integer -- needed to check the game fits the class period")

    return errors, warnings


RESPONSE_TYPE_LABELS = {
    "worksheet": "Nhiệm vụ",
    "homework": "Câu",
    "game": "Câu hỏi/Nhiệm vụ",
}


def to_markdown(material: dict) -> str:
    material_type = material["material_type"]
    title = {
        "worksheet": "PHIẾU HỌC TẬP",
        "homework": "PHIẾU BÀI TẬP",
        "game": "TRÒ CHƠI HỌC TẬP",
    }[material_type]

    lines = [
        f"# {title}: {material['topic']}",
        "",
        f"**Môn**: {material['subject']} | **Khối/Lớp**: {material['grade']}",
        "",
    ]

    if material_type == "game":
        duration = material.get("estimated_duration_minutes", "?")
        lines.extend([
            f"**Thời lượng dự kiến**: {duration} phút",
            "",
            "## Luật chơi",
            "",
            str(material.get("rules", "")),
            "",
        ])

    label = RESPONSE_TYPE_LABELS[material_type]
    lines.append("## Nội dung")
    for i, item in enumerate(material.get("items", []), start=1):
        if not isinstance(item, dict):
            continue
        lines.append("")
        lines.append(f"**{label} {i}**: {item.get('task', '')}")
        response_type = item.get("expected_response_type")
        if response_type:
            lines.append(f"- Dạng trả lời: {response_type}")
        difficulty = item.get("difficulty")
        if difficulty:
            lines.append(f"- Độ khó: {difficulty}")
        response_space = item.get("response_space")
        if response_space:
            lines.append(f"- Chỗ điền: {response_space}")
        hint = item.get("hint")
        if hint:
            lines.append(f"- Gợi ý: {hint}")

    answers = [(i, item) for i, item in enumerate(material.get("items", []), start=1)
               if isinstance(item, dict) and str(item.get("answer", "")).strip()]
    if answers:
        lines.extend(["", "## Đáp án / Hướng dẫn giải", ""])
        for i, item in answers:
            lines.append(f"- **{label} {i}**: {item.get('answer', '')}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("material", type=Path, help="Path to a classroom-material JSON file (see assets/material_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render Markdown to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        material = json.loads(args.material.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(material, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(material)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: structurally complete. This confirms structure only, not pedagogical quality or content accuracy.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(material), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
