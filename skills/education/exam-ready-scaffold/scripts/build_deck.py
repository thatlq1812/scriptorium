#!/usr/bin/env python3
"""Deterministic flashcard/quiz-item builder from a caller-supplied topic/
fact list. Never invents question content -- every term and definition comes
from the caller's own facts.json; this script only structures it into
flashcards and, for the mcq mode, into multiple-choice items whose distractor
choices are OTHER real definitions from the same supplied fact list (never a
fabricated wrong answer), selected by a fixed deterministic rule (list order,
no randomness) so the same input always produces the same output.

Mirrors assessment-builder's non-AI-content-generation posture (build_exam_matrix.py
balances counts/points but never writes question text) applied to a simpler,
content-neutral case: here the "content" (term/definition pairs) is always
caller-supplied; this script only reshapes it into study-ready items.

Usage:
    python build_deck.py <facts.json> [--mode flashcards|mcq|both] -o deck.json [--force]

facts.json:
    {
      "topic": "Cell biology",
      "facts": [
        {"term": "Mitochondria", "definition": "The organelle that produces ATP through cellular respiration."},
        {"term": "Nucleus", "definition": "The organelle that houses the cell's genetic material."}
      ]
    }

Exit 0 = deck built, exit 1 = valid input but requested mode not achievable
(e.g. mcq requested with fewer than 4 facts), exit 2 = malformed input or
output path exists without --force.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_MODES = {"flashcards", "mcq", "both"}
MIN_FACTS_FOR_MCQ = 4
ANSWER_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H"]


def load_facts(path: Path) -> dict:
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


def validate_facts_input(data: dict) -> list:
    """Returns the validated facts list, or raises ValueError naming exactly
    what's wrong."""
    if "facts" not in data:
        raise ValueError("missing required top-level key 'facts'.")
    facts = data["facts"]
    if not isinstance(facts, list) or not facts:
        raise ValueError("'facts' must be a non-empty list.")

    seen_terms: set[str] = set()
    for i, fact in enumerate(facts):
        if not isinstance(fact, dict):
            raise ValueError(f"facts[{i}] must be an object, got {type(fact).__name__}.")
        term = fact.get("term")
        definition = fact.get("definition")
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"facts[{i}].term is required and must be a non-empty string.")
        if not isinstance(definition, str) or not definition.strip():
            raise ValueError(f"facts[{i}].definition is required and must be a non-empty string.")
        normalized = term.strip().lower()
        if normalized in seen_terms:
            raise ValueError(f"facts[{i}].term ({term!r}) duplicates an earlier term (case/whitespace-insensitive).")
        seen_terms.add(normalized)

    return facts


def build_flashcards(facts: list) -> list:
    return [
        {"term": f["term"].strip(), "definition": f["definition"].strip()}
        for f in facts
    ]


def build_mcq(facts: list) -> list:
    """One MCQ per fact: the correct definition plus 3 distractor definitions
    drawn from the NEXT 3 facts in list order (wrapping around, skipping
    self) -- always real caller-supplied content, never invented. Choice
    ORDER within an item is a fixed rotation keyed on the fact's own index
    (not randomness), so build_deck.py is fully deterministic: same input,
    same output, every run."""
    n = len(facts)
    items = []
    for i, fact in enumerate(facts):
        correct_def = fact["definition"].strip()
        distractor_indices = []
        offset = 1
        while len(distractor_indices) < 3:
            candidate = (i + offset) % n
            if candidate != i:
                distractor_indices.append(candidate)
            offset += 1
        distractor_defs = [facts[j]["definition"].strip() for j in distractor_indices]

        # Fixed deterministic rotation: correct answer placed at position
        # (i % 4) among the 4 choices, others filled in distractor order.
        choices = [None, None, None, None]
        correct_position = i % 4
        choices[correct_position] = correct_def
        remaining_slots = [p for p in range(4) if p != correct_position]
        for slot, d in zip(remaining_slots, distractor_defs):
            choices[slot] = d

        items.append({
            "question": f"Which definition matches '{fact['term'].strip()}'?",
            "topic": fact.get("topic"),
            "choices": choices,
            "answer": ANSWER_LABELS[correct_position],
        })
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("facts_path", type=Path, help="Path to facts.json")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="both")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output deck.json path")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    args = parser.parse_args()

    try:
        data = load_facts(args.facts_path)
        facts = validate_facts_input(data)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output.exists() and not args.force:
        print(f"ERROR: {args.output} already exists. Use --force to overwrite.", file=sys.stderr)
        return 2

    deck: dict = {"topic": data.get("topic"), "source_fact_count": len(facts)}

    if args.mode in ("flashcards", "both"):
        deck["flashcards"] = build_flashcards(facts)

    if args.mode in ("mcq", "both"):
        if len(facts) < MIN_FACTS_FOR_MCQ:
            print(
                f"ERROR: mcq mode requires at least {MIN_FACTS_FOR_MCQ} facts to build "
                f"4-choice items with real distractors, got {len(facts)}.",
                file=sys.stderr,
            )
            return 1
        deck["mcq"] = build_mcq(facts)

    try:
        args.output.write_text(json.dumps(deck, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: could not write {args.output}: {exc}", file=sys.stderr)
        return 2

    parts = []
    if "flashcards" in deck:
        parts.append(f"{len(deck['flashcards'])} flashcard(s)")
    if "mcq" in deck:
        parts.append(f"{len(deck['mcq'])} mcq item(s)")
    print(f"OK: wrote {args.output} -- {', '.join(parts)}, from {len(facts)} supplied fact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
