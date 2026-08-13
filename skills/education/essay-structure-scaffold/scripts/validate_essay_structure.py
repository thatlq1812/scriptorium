#!/usr/bin/env python3
"""Structural validator for an academic essay outline: checks a thesis
statement is present, every body paragraph carries a topic sentence,
supporting evidence, and an explicit link back to the thesis, and the
conclusion restates the thesis without introducing content absent from the
rest of the outline. Stdlib only, local, deterministic -- no AI/network call
of any kind.

This checks STRUCTURE and lexical overlap only -- it never judges whether
the thesis is a good argument, whether the evidence is actually convincing,
or whether the writing itself is well-crafted; that stays the writer's (or
the writer's reviewer's) call. Errors block (exit 1); warnings are lexical
heuristics worth reviewing but never block (exit 0 with warnings printed).

Usage:
    python validate_essay_structure.py outline.json [--render outline.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TOP_FIELDS = ("thesis_statement", "body_paragraphs", "conclusion")

# Deliberately small, general English stopword list -- enough to strip noise
# words from the lexical overlap/new-claim heuristics below without
# pretending to be a real NLP stopword corpus. Reviewed manually against the
# fixtures used to verify this script; not sourced from any external list.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "nor", "for", "so", "yet",
    "of", "in", "on", "at", "to", "from", "by", "with", "about", "as",
    "is", "are", "was", "were", "be", "been", "being", "this", "that",
    "these", "those", "it", "its", "which", "who", "whom", "whose",
    "not", "no", "than", "then", "also", "into", "over", "under",
    "again", "further", "there", "here", "such", "very", "can", "will",
    "would", "should", "could", "may", "might", "must", "shall",
    "has", "have", "had", "do", "does", "did", "if", "because", "while",
    "when", "where", "how", "what", "each", "both", "more", "most",
    "other", "some", "own", "same", "just", "only",
}

WORD_RE = re.compile(r"[A-Za-z']+")


class EssayError(Exception):
    pass


def _content_words(text: str) -> set[str]:
    """Lowercased, stopword-filtered content words (len > 2) -- the same
    lexical unit used for both the new-claim and thesis-link heuristics."""
    words = {w.lower() for w in WORD_RE.findall(text)}
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def validate(outline: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    missing = [f for f in REQUIRED_TOP_FIELDS if f not in outline]
    if missing:
        errors.append(f"missing required field(s): {', '.join(missing)}")
        return errors, warnings

    thesis = outline["thesis_statement"]
    if not isinstance(thesis, str) or not thesis.strip():
        errors.append("thesis_statement must be a non-empty string")
        thesis = ""

    body_paragraphs = outline["body_paragraphs"]
    if not isinstance(body_paragraphs, list) or not body_paragraphs:
        errors.append("body_paragraphs must be a non-empty list")
        body_paragraphs = []

    supporting_text_parts = [thesis]
    valid_paragraphs: list[dict] = []

    for i, para in enumerate(body_paragraphs):
        if not isinstance(para, dict):
            errors.append(f"body_paragraphs[{i}] must be an object")
            continue

        topic_sentence = para.get("topic_sentence")
        if not isinstance(topic_sentence, str) or not topic_sentence.strip():
            errors.append(f"body_paragraphs[{i}]: topic_sentence is required and must be non-empty")
            topic_sentence = ""

        evidence = para.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"body_paragraphs[{i}]: evidence must be a non-empty list")
            evidence = []
        else:
            for j, ev in enumerate(evidence):
                if not isinstance(ev, str) or not ev.strip():
                    errors.append(f"body_paragraphs[{i}].evidence[{j}]: must be a non-empty string")

        link_back = para.get("link_back_to_thesis")
        if not isinstance(link_back, str) or not link_back.strip():
            errors.append(f"body_paragraphs[{i}]: link_back_to_thesis is required and must be non-empty")
            link_back = ""

        if topic_sentence and evidence and link_back:
            valid_paragraphs.append(para)

        supporting_text_parts.append(topic_sentence)
        supporting_text_parts.extend(e for e in evidence if isinstance(e, str))

        # Lexical heuristic: link_back_to_thesis sharing zero content words
        # with the thesis statement is a signal (not proof) the paragraph
        # never actually ties back to the thesis.
        if thesis and link_back:
            thesis_words = _content_words(thesis)
            link_words = _content_words(link_back)
            if thesis_words and link_words and not (thesis_words & link_words):
                warnings.append(
                    f"body_paragraphs[{i}]: link_back_to_thesis shares no content words with "
                    f"thesis_statement -- may not actually reference the thesis (lexical heuristic, review manually)"
                )

    conclusion = outline["conclusion"]
    if not isinstance(conclusion, dict):
        errors.append("conclusion must be an object")
        conclusion = {}

    restates_thesis = conclusion.get("restates_thesis") if isinstance(conclusion, dict) else None
    if not isinstance(restates_thesis, str) or not restates_thesis.strip():
        errors.append("conclusion.restates_thesis is required and must be non-empty")
        restates_thesis = ""

    if thesis and restates_thesis:
        supporting_words: set[str] = set()
        for part in supporting_text_parts:
            if isinstance(part, str):
                supporting_words |= _content_words(part)

        conclusion_words = _content_words(restates_thesis)
        new_words = conclusion_words - supporting_words
        if new_words:
            warnings.append(
                "conclusion.restates_thesis contains word(s) not found anywhere in the thesis or body "
                f"paragraphs, a possible sign of a new claim introduced in the conclusion: {sorted(new_words)} "
                "(lexical heuristic -- paraphrased new claims and legitimate synonyms both look identical to "
                "this check, review manually)"
            )

    return errors, warnings


def to_markdown(outline: dict) -> str:
    lines = ["# Essay Structure Outline", ""]
    lines.append("## Thesis Statement")
    lines.append(outline.get("thesis_statement", ""))
    lines.append("")

    lines.append("## Body Paragraphs")
    for i, para in enumerate(outline.get("body_paragraphs", []), start=1):
        lines.append(f"### Paragraph {i}")
        lines.append(f"**Topic sentence**: {para.get('topic_sentence', '')}")
        lines.append("")
        lines.append("**Evidence**:")
        for ev in para.get("evidence", []):
            lines.append(f"- {ev}")
        lines.append("")
        lines.append(f"**Link back to thesis**: {para.get('link_back_to_thesis', '')}")
        lines.append("")

    lines.append("## Conclusion")
    conclusion = outline.get("conclusion", {})
    lines.append(conclusion.get("restates_thesis", "") if isinstance(conclusion, dict) else "")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("outline", type=Path, help="Path to an essay outline JSON file (see assets/outline_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render a Markdown outline to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        outline = json.loads(args.outline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(outline, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(outline)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: structurally complete -- thesis present, every body paragraph has a topic sentence, "
          "evidence, and a link back to the thesis, conclusion restates the thesis. This confirms "
          "structure and lexical heuristics only, not argument quality.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(outline), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
