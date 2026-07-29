#!/usr/bin/env python3
"""Validate a Master's/PhD dissertation-proposal document JSON record for
structural completeness against the standard five-part graduate proposal
shape (problem statement, literature gap, research questions, methodology,
timeline), then optionally render it to clean Markdown. Same
structural-completeness shape as legal-research-brief's validator, adapted
to academic-proposal structure instead of legal-brief structure -- but this
skill has no grounding/citation requirement (unlike legal-research-brief),
since a proposal's own required sections are a fixed document-structure
check, not a claim-by-claim sourcing check.

Stdlib only (json, argparse), local, deterministic -- no AI/LLM/network
call of any kind. Never judges whether the content is intellectually
sound, novel, or feasible -- structural completeness only.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_proposal.py proposal.json [--render proposal.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TEXT_FIELDS = ["problem_statement", "literature_gap", "methodology"]


class ProposalError(Exception):
    pass


def load_proposal(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProposalError(f"cannot read proposal file: {exc}") from exc
    if not isinstance(data, dict):
        raise ProposalError("top-level proposal JSON must be an object")
    return data


def validate(proposal: dict) -> list[str]:
    errors: list[str] = []

    if not proposal.get("title") or not isinstance(proposal.get("title"), str):
        errors.append("title is required")

    for field in REQUIRED_TEXT_FIELDS:
        value = proposal.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string")

    research_questions = proposal.get("research_questions")
    if not isinstance(research_questions, list) or not research_questions:
        errors.append("research_questions must be a non-empty list")
    else:
        for i, q in enumerate(research_questions):
            if not isinstance(q, str) or not q.strip():
                errors.append(f"research_questions[{i}] must be a non-empty string")

    timeline = proposal.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        errors.append("timeline must be a non-empty list of milestones")
    else:
        for i, m in enumerate(timeline):
            if not isinstance(m, dict):
                errors.append(f"timeline[{i}] must be an object with 'milestone' and 'target_date'")
                continue
            if not m.get("milestone") or not isinstance(m.get("milestone"), str):
                errors.append(f"timeline[{i}]: milestone is required and must be a non-empty string")
            if not m.get("target_date") or not isinstance(m.get("target_date"), str):
                errors.append(f"timeline[{i}]: target_date is required and must be a non-empty string")

    return errors


def to_markdown(proposal: dict) -> str:
    lines = [f"# {proposal['title']}", ""]
    if proposal.get("degree_level"):
        lines.extend([f"**Degree level:** {proposal['degree_level']}", ""])
    lines.extend(["## Problem Statement", "", proposal["problem_statement"], ""])
    lines.extend(["## Literature Gap", "", proposal["literature_gap"], ""])
    lines.extend(["## Research Questions", ""])
    for q in proposal["research_questions"]:
        lines.append(f"- {q}")
    lines.extend(["", "## Methodology", "", proposal["methodology"], ""])
    lines.extend(["## Timeline", ""])
    for m in proposal["timeline"]:
        lines.append(f"- **{m['target_date']}**: {m['milestone']}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("proposal", type=Path, help="Path to a proposal JSON file (see assets/proposal_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        proposal = load_proposal(args.proposal)
    except ProposalError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    errors = validate(proposal)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"VALID: {proposal.get('title')!r} has all 5 required sections "
          f"({len(proposal['research_questions'])} research question(s), "
          f"{len(proposal['timeline'])} timeline milestone(s)).")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(proposal), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
