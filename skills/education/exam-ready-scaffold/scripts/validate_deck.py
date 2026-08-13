#!/usr/bin/env python3
"""Structural validator for a flashcard/MCQ deck (the output of build_deck.py,
or a hand-authored deck following the same schema). Checks structure and
arithmetic/label consistency only -- never judges whether a definition is
factually correct or whether a distractor is a "good" wrong answer; that
content-quality judgment stays with whoever supplied the facts.

Usage:
    python validate_deck.py <deck.json>

deck.json:
    {
      "topic": "...",              # optional
      "flashcards": [{"term": "...", "definition": "..."}, ...],   # optional
      "mcq": [{"question": "...", "choices": ["...", "...", "...", "..."], "answer": "A"}, ...]  # optional
    }

At least one of "flashcards" / "mcq" must be present and non-empty.

Exit 0 = structurally valid, exit 1 = one or more violations (each printed
with the exact index/field), exit 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ANSWER_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H"]


def load_deck(path: Path) -> dict:
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


def validate_flashcards(flashcards) -> list[str]:
    errors: list[str] = []
    if not isinstance(flashcards, list) or not flashcards:
        return ["'flashcards' must be a non-empty list."]

    seen_terms: set[str] = set()
    for i, card in enumerate(flashcards):
        if not isinstance(card, dict):
            errors.append(f"flashcards[{i}] must be an object, got {type(card).__name__}.")
            continue
        term = card.get("term")
        definition = card.get("definition")
        if not isinstance(term, str) or not term.strip():
            errors.append(f"flashcards[{i}].term is missing or empty.")
        else:
            normalized = term.strip().lower()
            if normalized in seen_terms:
                errors.append(f"flashcards[{i}].term ({term!r}) duplicates an earlier term.")
            seen_terms.add(normalized)
        if not isinstance(definition, str) or not definition.strip():
            errors.append(f"flashcards[{i}].definition is missing or empty.")
    return errors


def validate_mcq(mcq) -> list[str]:
    errors: list[str] = []
    if not isinstance(mcq, list) or not mcq:
        return ["'mcq' must be a non-empty list."]

    for i, item in enumerate(mcq):
        if not isinstance(item, dict):
            errors.append(f"mcq[{i}] must be an object, got {type(item).__name__}.")
            continue

        question = item.get("question")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"mcq[{i}].question is missing or empty.")

        choices = item.get("choices")
        if not isinstance(choices, list):
            errors.append(f"mcq[{i}].choices must be a list, got {type(choices).__name__}.")
            continue
        if len(choices) != 4:
            errors.append(f"mcq[{i}].choices has {len(choices)} entries, must have exactly 4.")
        non_empty = [c for c in choices if isinstance(c, str) and c.strip()]
        if len(non_empty) != len(choices):
            errors.append(f"mcq[{i}].choices contains an empty or non-string entry.")
        normalized = [c.strip().lower() for c in non_empty]
        if len(set(normalized)) != len(normalized):
            errors.append(f"mcq[{i}].choices contains duplicate choices (case/whitespace-insensitive).")

        answer = item.get("answer")
        valid_labels = ANSWER_LABELS[: len(choices)]
        if not isinstance(answer, str) or answer not in valid_labels:
            errors.append(
                f"mcq[{i}].answer ({answer!r}) must be one of {valid_labels} "
                f"(matching the number of choices)."
            )
    return errors


def validate_deck(data: dict) -> list[str]:
    has_flashcards = "flashcards" in data
    has_mcq = "mcq" in data

    if not has_flashcards and not has_mcq:
        return ["deck must contain at least one of 'flashcards' or 'mcq'."]

    errors: list[str] = []
    if has_flashcards:
        errors.extend(validate_flashcards(data["flashcards"]))
    if has_mcq:
        errors.extend(validate_mcq(data["mcq"]))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck_path", type=Path, help="Path to deck.json")
    args = parser.parse_args()

    try:
        data = load_deck(args.deck_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate_deck(data)

    if errors:
        print(f"INVALID: {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    parts = []
    if "flashcards" in data:
        parts.append(f"{len(data['flashcards'])} flashcard(s)")
    if "mcq" in data:
        parts.append(f"{len(data['mcq'])} mcq item(s)")
    print(f"OK: deck is structurally valid -- {', '.join(parts)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
