#!/usr/bin/env python3
"""Validate a deep-research brief JSON record against a strict-grounding
requirement: every finding must cite at least one caller-declared source,
every cited source id must actually exist, and every inline [S..] citation
marker used in the prose synthesis must also resolve to a real source.
Stdlib only (json, argparse, re) -- no AI/LLM/network call, and this script
never searches anything itself; it only checks that a research brief someone
(the calling agent, doing its own research using its own tools) already
produced is honestly sourced.

Same discipline as this project's legal-research-brief and
citation-management skills, generalized beyond the legal domain: a
fabricated or mistyped citation is a hard error, not a warning.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_research_brief.py <brief.json> [--render brief.md]
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

CITATION_MARKER_RE = re.compile(r"\[(S[\w-]+)\]")
CONFIDENCE_LEVELS = {"high", "medium", "low"}
REQUIRED_TEXT_FIELDS = ["gaps", "contradictions", "confidence_rationale"]


class BriefError(Exception):
    pass


def load_brief(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BriefError(f"cannot read brief.json: {exc}") from exc
    if not isinstance(data, dict):
        raise BriefError("top-level brief JSON must be an object")
    return data


def validate(brief: dict) -> list[str]:
    errors: list[str] = []

    if not brief.get("question"):
        errors.append("question is required")

    sub_questions = brief.get("sub_questions")
    if not isinstance(sub_questions, list) or not sub_questions:
        errors.append("sub_questions must be a non-empty list")

    sources = brief.get("sources")
    valid_ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
    else:
        for i, s in enumerate(sources):
            if not isinstance(s, dict) or not s.get("id") or not s.get("title"):
                errors.append(f"sources[{i}] must be an object with a non-empty 'id' and 'title'")
                continue
            if s["id"] in valid_ids:
                errors.append(f"duplicate source id: {s['id']!r}")
                continue
            if not s.get("accessed"):
                errors.append(f"sources[{i}] ({s['id']}): 'accessed' date is required -- a source found today may say something different tomorrow")
            valid_ids.add(s["id"])

    findings = brief.get("findings")
    if not isinstance(findings, list) or not findings:
        errors.append("findings must be a non-empty list")
    else:
        for i, f in enumerate(findings):
            if not isinstance(f, dict) or not f.get("claim"):
                errors.append(f"findings[{i}]: claim is required")
                continue
            cites = f.get("cites")
            if not isinstance(cites, list) or not cites:
                errors.append(f"findings[{i}] ({f['claim'][:40]!r}...): cites is required and must be non-empty -- every finding must trace to a source")
                continue
            for src_id in cites:
                if src_id not in valid_ids:
                    errors.append(f"findings[{i}]: cites source id {src_id!r} which does not exist in sources -- likely a fabricated or mistyped citation")

    for field in REQUIRED_TEXT_FIELDS:
        if not brief.get(field):
            errors.append(f"{field} is required (state 'none identified' explicitly if that's the honest answer -- don't omit the field)")

    confidence = brief.get("confidence")
    if confidence not in CONFIDENCE_LEVELS:
        errors.append(f"confidence must be one of {sorted(CONFIDENCE_LEVELS)}, got {confidence!r}")

    synthesis = brief.get("synthesis")
    if not synthesis:
        errors.append("synthesis is required")
    else:
        markers = set(CITATION_MARKER_RE.findall(synthesis))
        if not markers:
            errors.append("synthesis must contain at least one inline [S..] citation marker -- a synthesis with zero citations is an unsourced narrative, not a research finding")
        for marker in markers:
            if marker not in valid_ids:
                errors.append(f"synthesis cites {marker!r} inline which does not exist in sources -- likely a fabricated or mistyped citation")

    return errors


def to_markdown(brief: dict) -> str:
    sources_by_id = {s["id"]: s for s in brief["sources"]}

    def cite(ids: list[str]) -> str:
        return " [" + ", ".join(ids) + "]"

    lines = [
        "# Research Brief",
        "",
        "## Question",
        "",
        brief["question"],
        "",
        "## Sub-questions",
        "",
    ]
    lines.extend(f"- {q}" for q in brief["sub_questions"])
    lines.extend(["", "## Findings", ""])
    for f in brief["findings"]:
        lines.append(f"- {f['claim']}{cite(f['cites'])}")
    lines.extend(["", "## Synthesis", "", brief["synthesis"]])
    lines.extend([
        "", "## Gaps", "", brief["gaps"],
        "", "## Contradictions", "", brief["contradictions"],
        "", f"## Confidence: {brief['confidence']}", "", brief["confidence_rationale"],
        "", "## Sources", "",
    ])
    for sid, s in sources_by_id.items():
        url = f" — {s['url']}" if s.get("url") else ""
        lines.append(f"- **{sid}**: {s['title']}{url} (accessed {s['accessed']})")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("brief", type=Path, help="Path to a research brief JSON file (see assets/research_brief_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.brief.exists():
        print(f"Input not found: {args.brief}", file=sys.stderr)
        return 1

    try:
        brief = load_brief(args.brief)
    except BriefError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    errors = validate(brief)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: every finding and every inline synthesis citation traces to a real, declared source. This confirms grounding/structure only, not that the research is complete or correct.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(brief), encoding="utf-8", newline="\n")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
