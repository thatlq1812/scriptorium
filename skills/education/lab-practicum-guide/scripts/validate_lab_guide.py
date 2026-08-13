#!/usr/bin/env python3
"""Validate a lab-session practicum guide JSON record and, optionally,
render it to clean Markdown. Structural validator only -- content
(the actual safety wording, procedure text, expected outcomes) is always
caller-supplied; this script never judges whether a safety note is
actually sufficient or whether a step's science is correct. Stdlib only
(json, argparse), local, deterministic -- no AI/LLM/network call of any
kind.

Checks:
  - safety_notes is a non-empty list of non-empty strings (every academic
    lab manual convention -- e.g. ACS "Guidelines for Chemical Laboratory
    Safety in Academic Institutions" and standard university lab-safety-plan
    templates -- requires a stated safety section before procedure steps;
    this script only checks the section is PRESENT and non-empty, not that
    it is complete or correct).
  - equipment is a non-empty list of non-empty strings.
  - steps is a non-empty list; each step has a unique, sequential
    step_number starting at 1, a non-empty instruction, and a non-empty
    expected_outcome (the standard "procedure + checkpoint" shape used in
    lab-practicum manuals so a student/TA can verify the step actually
    worked before moving on).
  - every equipment_used entry named in a step must be declared in the
    top-level equipment list (hard error, catches a typo'd/undeclared
    equipment reference -- same "flag an undeclared key" discipline as
    legal-form-filler's fill_form.py).
  - a declared equipment item never referenced by any step is a WARNING
    (not an error) -- may be legitimately optional/backup equipment.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_lab_guide.py guide.json [--render guide.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class GuideError(Exception):
    pass


def load_guide(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuideError(f"cannot read guide file: {exc}") from exc
    if not isinstance(data, dict):
        raise GuideError("top-level guide JSON must be an object")
    return data


def validate(guide: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not guide.get("title"):
        errors.append("title is required")

    safety_notes = guide.get("safety_notes")
    if not isinstance(safety_notes, list) or not safety_notes:
        errors.append("safety_notes must be a non-empty list")
    else:
        for i, note in enumerate(safety_notes):
            if not isinstance(note, str) or not note.strip():
                errors.append(f"safety_notes[{i}] must be a non-empty string")

    equipment = guide.get("equipment")
    equipment_set: set[str] = set()
    if not isinstance(equipment, list) or not equipment:
        errors.append("equipment must be a non-empty list")
    else:
        for i, item in enumerate(equipment):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"equipment[{i}] must be a non-empty string")
                continue
            if item in equipment_set:
                errors.append(f"equipment[{i}]: duplicate equipment item {item!r}")
            equipment_set.add(item)

    steps = guide.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty list")
        return errors, warnings

    seen_numbers: set[int] = set()
    used_equipment: set[str] = set()
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"steps[{i}] must be an object")
            continue

        step_number = step.get("step_number")
        if not isinstance(step_number, int) or isinstance(step_number, bool):
            errors.append(f"steps[{i}]: step_number is required and must be an integer")
        else:
            if step_number in seen_numbers:
                errors.append(f"steps[{i}]: duplicate step_number {step_number}")
            seen_numbers.add(step_number)

        if not step.get("instruction") or not isinstance(step.get("instruction"), str):
            errors.append(f"steps[{i}] (step_number={step.get('step_number')!r}): instruction is required")

        if not step.get("expected_outcome") or not isinstance(step.get("expected_outcome"), str):
            errors.append(
                f"steps[{i}] (step_number={step.get('step_number')!r}): expected_outcome is required "
                f"-- every step needs a clear checkpoint a student/TA can verify"
            )

        equipment_used = step.get("equipment_used", [])
        if equipment_used and not isinstance(equipment_used, list):
            errors.append(f"steps[{i}]: equipment_used must be a list if present")
        elif equipment_used:
            for item in equipment_used:
                if item not in equipment_set:
                    errors.append(
                        f"steps[{i}] (step_number={step.get('step_number')!r}): equipment_used references "
                        f"{item!r} which is not declared in the top-level equipment list"
                    )
                else:
                    used_equipment.add(item)

    if seen_numbers and seen_numbers != set(range(1, len(seen_numbers) + 1)):
        expected = list(range(1, len(steps) + 1))
        errors.append(
            f"step_number values must be sequential starting at 1 with no gaps -- got {sorted(seen_numbers)}, "
            f"expected {expected}"
        )

    unused = equipment_set - used_equipment
    for item in sorted(unused):
        warnings.append(f"equipment {item!r} is declared but never referenced by any step's equipment_used")

    return errors, warnings


def to_markdown(guide: dict) -> str:
    lines = [f"# {guide['title']}", ""]
    if guide.get("course"):
        lines.extend([f"**Course:** {guide['course']}", ""])
    lines.extend(["## Safety Notes", ""])
    for note in guide["safety_notes"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Equipment", ""])
    for item in guide["equipment"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Procedure", ""])
    for step in sorted(guide["steps"], key=lambda s: s["step_number"]):
        lines.append(f"### Step {step['step_number']}")
        lines.append("")
        lines.append(step["instruction"])
        if step.get("equipment_used"):
            lines.append("")
            lines.append(f"**Equipment used:** {', '.join(step['equipment_used'])}")
        lines.append("")
        lines.append(f"**Expected outcome:** {step['expected_outcome']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("guide", type=Path, help="Path to a lab guide JSON file (see assets/lab_guide_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        guide = load_guide(args.guide)
    except GuideError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate(guide)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"VALID: {guide.get('title')!r} -- {len(guide['steps'])} steps, "
          f"{len(guide['safety_notes'])} safety note(s), {len(guide['equipment'])} equipment item(s).")
    if warnings:
        print(f"WARNING: {len(warnings)} flag(s) -- not blocking:")
        for w in warnings:
            print(f"  - {w}")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(guide), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
