#!/usr/bin/env python3
"""Validate a structured contract risk-review log: every issue must name a
clause, a concern, a specific recommended action, and a severity; the log
must be explicit about whether a systematic review actually happened (an
empty issues list is ambiguous between "not reviewed" and "reviewed, found
nothing" unless flagged). Stdlib only (json, argparse), local,
deterministic -- no AI/network call of any kind.

This does NOT auto-detect contract risk. Identifying whether a clause is
actually risky requires legal judgment this project does not attempt to
automate (same reasoning as peer-review's claim-evidence matrix: a
structured completeness check on human/agent-authored analysis, not a
substitute for it). It only validates that a review log is structurally
complete and internally consistent -- never that the risk assessment
itself is correct.

Exit codes: 0 = structurally valid, 1 = errors found, 2 = malformed input.

Usage:
    python validate_risk_log.py risk_log.json [--render risk_log.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_SEVERITIES = {"low", "medium", "high"}
KNOWN_RISK_CATEGORIES = {
    "payment", "liability", "termination", "ip", "confidentiality",
    "compliance", "indemnification", "dispute_resolution", "force_majeure", "other",
}


def validate(log: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("contract_title", "reviewed_by", "review_date"):
        if not log.get(field):
            errors.append(f"{field} is required")

    clauses_reviewed = log.get("clauses_reviewed")
    if not isinstance(clauses_reviewed, list) or not clauses_reviewed:
        errors.append("clauses_reviewed must be a non-empty list -- declares that a systematic review actually happened, not just an ad-hoc glance")

    issues = log.get("issues")
    no_issues_flag = log.get("no_issues_found_after_review")

    if not isinstance(issues, list):
        errors.append("issues must be a list (use [] with no_issues_found_after_review=true if the review found nothing)")
        issues = []

    if not issues:
        if no_issues_flag is not True:
            errors.append("issues is empty but no_issues_found_after_review is not explicitly true -- an empty issues list is ambiguous between 'not reviewed' and 'reviewed, found nothing', must be explicit")
    else:
        if no_issues_flag is True:
            errors.append("no_issues_found_after_review is true but issues is non-empty -- contradictory")

    seen_ids: set[str] = set()
    reviewed_set = set(clauses_reviewed) if isinstance(clauses_reviewed, list) else set()

    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            errors.append(f"issues[{i}] must be an object")
            continue

        issue_id = issue.get("id")
        if not issue_id:
            errors.append(f"issues[{i}]: id is required")
        elif issue_id in seen_ids:
            errors.append(f"issues[{i}]: duplicate id {issue_id!r}")
        else:
            seen_ids.add(issue_id)

        clause = issue.get("clause_location")
        if not clause:
            errors.append(f"issues[{i}] ({issue_id}): clause_location is required")
        elif reviewed_set and clause not in reviewed_set:
            warnings.append(f"issues[{i}] ({issue_id}): clause_location {clause!r} is not in clauses_reviewed -- was this clause actually reviewed?")

        severity = issue.get("severity")
        if severity not in VALID_SEVERITIES:
            errors.append(f"issues[{i}] ({issue_id}): severity must be one of {sorted(VALID_SEVERITIES)}, got {severity!r}")

        category = issue.get("risk_category")
        if not category:
            errors.append(f"issues[{i}] ({issue_id}): risk_category is required")
        elif category not in KNOWN_RISK_CATEGORIES:
            warnings.append(f"issues[{i}] ({issue_id}): risk_category {category!r} is not in the known set {sorted(KNOWN_RISK_CATEGORIES)} -- verify it's intentional, not a typo")

        if not issue.get("concern"):
            errors.append(f"issues[{i}] ({issue_id}): concern is required")

        action = issue.get("recommended_action")
        if not action:
            errors.append(f"issues[{i}] ({issue_id}): recommended_action is required")
        elif action.strip().lower() in ("review this", "review", "check this", "tbd", "n/a"):
            warnings.append(f"issues[{i}] ({issue_id}): recommended_action {action!r} is too vague to be actionable -- state a specific fix or negotiation point")

    return errors, warnings


def to_markdown(log: dict) -> str:
    lines = [
        f"# Contract Risk Log: {log['contract_title']}",
        "",
        f"**Reviewed by**: {log['reviewed_by']} | **Date**: {log['review_date']}",
        "",
        f"**Clauses reviewed**: {', '.join(log.get('clauses_reviewed', []))}",
        "",
    ]
    issues = log.get("issues", [])
    if not issues:
        lines.append("No issues found after systematic review.")
    else:
        lines.extend(["| ID | Clause | Category | Severity | Concern | Recommended Action |", "| --- | --- | --- | --- | --- | --- |"])
        for issue in issues:
            lines.append(
                f"| {issue.get('id', '')} | {issue.get('clause_location', '')} | {issue.get('risk_category', '')} "
                f"| {issue.get('severity', '')} | {issue.get('concern', '')} | {issue.get('recommended_action', '')} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("risk_log", type=Path, help="Path to a risk log JSON file (see assets/risk_log_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        log = json.loads(args.risk_log.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(log, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(log)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: risk log is structurally complete. This confirms structure only, not the correctness of the risk assessment itself.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(log), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
