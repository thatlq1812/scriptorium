#!/usr/bin/env python3
"""Structural validator + Markdown renderer for a Cornell-notes or
mind-map-style structured note. The caller always supplies the actual
content (cues, notes, summary, branch labels) -- this script only checks
that the required structural fields are present and non-empty for the
declared note type, then renders a clean Markdown version. It never judges
whether the CONTENT is pedagogically sound or factually correct.

Usage:
    python validate_note.py <note.json> [--render note.md] [--force]

note.json (Cornell):
    {
      "type": "cornell",
      "title": "Photosynthesis",
      "topic": "Biology",             # optional
      "date": "2026-07-29",           # optional
      "entries": [
        {"cue": "What is photosynthesis?", "notes": "The process by which plants convert light energy into chemical energy stored in glucose."}
      ],
      "summary": "Photosynthesis converts light into chemical energy stored in glucose, using CO2 and water, releasing oxygen."
    }

note.json (mind map):
    {
      "type": "mindmap",
      "title": "Photosynthesis",
      "central_topic": "Photosynthesis",
      "branches": [
        {"label": "Inputs", "children": [{"label": "Sunlight", "children": []}, {"label": "Water", "children": []}]}
      ]
    }

Exit 0 = structurally valid, exit 1 = one or more violations (each printed
with the exact field/path), exit 2 = malformed input, unknown 'type', or
--render target exists without --force.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_TYPES = {"cornell", "mindmap"}


def load_note(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"{path} does not exist.")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object, got {type(data).__name__}.")
    return data


# ---------------------------------------------------------------------------
# Cornell
# ---------------------------------------------------------------------------

def validate_cornell(note: dict) -> list[str]:
    errors: list[str] = []

    title = note.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("'title' is required and must be a non-empty string.")

    entries = note.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("'entries' must be a non-empty list.")
    else:
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"entries[{i}] must be an object, got {type(entry).__name__}.")
                continue
            cue = entry.get("cue")
            notes = entry.get("notes")
            if not isinstance(cue, str) or not cue.strip():
                errors.append(f"entries[{i}].cue is missing or empty.")
            if not isinstance(notes, str) or not notes.strip():
                errors.append(f"entries[{i}].notes is missing or empty.")

    summary = note.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("'summary' is required and must be a non-empty string.")

    return errors


def render_cornell(note: dict) -> str:
    lines = [f"# {note['title'].strip()}", ""]
    if note.get("topic"):
        lines.append(f"**Topic:** {note['topic']}")
    if note.get("date"):
        lines.append(f"**Date:** {note['date']}")
    if note.get("topic") or note.get("date"):
        lines.append("")

    lines.append("## Cues / Notes")
    lines.append("")
    lines.append("| Cue | Notes |")
    lines.append("| --- | --- |")
    for entry in note["entries"]:
        cue = entry["cue"].strip().replace("|", "\\|")
        notes = entry["notes"].strip().replace("|", "\\|")
        lines.append(f"| {cue} | {notes} |")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(note["summary"].strip())
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mind map
# ---------------------------------------------------------------------------

def _validate_branch(branch, path: str, errors: list[str]) -> None:
    if not isinstance(branch, dict):
        errors.append(f"{path} must be an object, got {type(branch).__name__}.")
        return
    label = branch.get("label")
    if not isinstance(label, str) or not label.strip():
        errors.append(f"{path}.label is missing or empty.")
    children = branch.get("children", [])
    if not isinstance(children, list):
        errors.append(f"{path}.children must be a list (may be empty), got {type(children).__name__}.")
        return
    for i, child in enumerate(children):
        _validate_branch(child, f"{path}.children[{i}]", errors)


def validate_mindmap(note: dict) -> list[str]:
    errors: list[str] = []

    central_topic = note.get("central_topic")
    if not isinstance(central_topic, str) or not central_topic.strip():
        errors.append("'central_topic' is required and must be a non-empty string.")

    branches = note.get("branches")
    if not isinstance(branches, list) or not branches:
        errors.append("'branches' must be a non-empty list.")
    else:
        for i, branch in enumerate(branches):
            _validate_branch(branch, f"branches[{i}]", errors)

    return errors


def _render_branch(branch: dict, depth: int, lines: list[str]) -> None:
    indent = "  " * depth
    lines.append(f"{indent}- {branch['label'].strip()}")
    for child in branch.get("children", []):
        _render_branch(child, depth + 1, lines)


def render_mindmap(note: dict) -> str:
    lines = [f"# {note.get('title', note['central_topic']).strip()}", ""]
    lines.append(f"**Central topic:** {note['central_topic'].strip()}")
    lines.append("")
    for branch in note["branches"]:
        _render_branch(branch, 0, lines)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

VALIDATORS = {"cornell": validate_cornell, "mindmap": validate_mindmap}
RENDERERS = {"cornell": render_cornell, "mindmap": render_mindmap}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("note_path", type=Path, help="Path to note.json")
    parser.add_argument("--render", type=Path, default=None, help="Optional Markdown output path")
    parser.add_argument("--force", action="store_true", help="Overwrite --render target if it already exists")
    args = parser.parse_args()

    try:
        note = load_note(args.note_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    note_type = note.get("type")
    if note_type not in VALID_TYPES:
        print(
            f"ERROR: 'type' ({note_type!r}) must be one of {sorted(VALID_TYPES)}.",
            file=sys.stderr,
        )
        return 2

    if args.render is not None and args.render.exists() and not args.force:
        print(f"ERROR: {args.render} already exists. Use --force to overwrite.", file=sys.stderr)
        return 2

    errors = VALIDATORS[note_type](note)

    if errors:
        print(f"INVALID ({note_type}): {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {note_type} note is structurally valid.")

    if args.render is not None:
        rendered = RENDERERS[note_type](note)
        try:
            args.render.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: could not write {args.render}: {exc}", file=sys.stderr)
            return 2
        print(f"Rendered Markdown written to {args.render}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
