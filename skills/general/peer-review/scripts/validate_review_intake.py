#!/usr/bin/env python3
"""Validate a completed review-intake JSON file (see
assets/review_intake_template.json) against the mandatory authorization,
confidentiality, and accountability gate — stdlib only, local, deterministic.
This validates DECLARATIONS, not their truth: it cannot verify that the
named authorization is real, only that the required fields were genuinely
filled in and no hard-blocking condition (external service use, data reuse,
unresolved conflicts) is declared.

A field still holding its template placeholder (`<...>`) counts as NOT
filled: copying the template and flipping the booleans must never pass this
gate.

Prints READY_FOR_LOCAL_REVIEW (proceed) or BLOCKED (with reasons) — do not
proceed with any manuscript inspection while BLOCKED.

Exit codes: 0 = READY_FOR_LOCAL_REVIEW, 1 = BLOCKED, 2 = malformed input.

Usage:
    python validate_review_intake.py completed-intake.json
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

VALID_REVIEW_MODELS = {"single-blind", "double-blind", "open", "other"}
PLACEHOLDER_RE = re.compile(r"^\s*<.*>\s*$", re.DOTALL)
NOT_CHECKED_RE = re.compile(r"\bnot checked\b|\bunknown\b|\bn/?a\b", re.I)


def is_filled(value: object) -> bool:
    """True only for a real, non-placeholder string."""
    return isinstance(value, str) and bool(value.strip()) and not PLACEHOLDER_RE.match(value)


def _section(intake: dict, name: str, reasons: list[str]) -> dict:
    section = intake.get(name)
    if not isinstance(section, dict):
        reasons.append(f"{name} object is required")
        return {}
    return section


def validate(intake: dict) -> list[str]:
    reasons: list[str] = []

    for field in ("submission_type", "review_question"):
        if not is_filled(intake.get(field)):
            reasons.append(f"{field} is required (still empty or unfilled template placeholder)")
    if intake.get("review_model") not in VALID_REVIEW_MODELS:
        reasons.append(f"review_model must be one of {sorted(VALID_REVIEW_MODELS)}")

    auth = _section(intake, "authorization", reasons)
    if auth:
        if not is_filled(auth.get("authorized_by")):
            reasons.append("authorization.authorized_by is required (undocumented authorization)")
        if not is_filled(auth.get("authorization_basis")):
            reasons.append("authorization.authorization_basis is required")
        if auth.get("venue_policy_checked") is not True:
            reasons.append("authorization.venue_policy_checked must be true (unchecked venue policy)")
        policy = auth.get("ai_tool_policy")
        if not is_filled(policy):
            reasons.append("authorization.ai_tool_policy is required — record what the venue's policy says about "
                           "AI-assisted review before using any tooling on the submission")
        elif NOT_CHECKED_RE.search(policy):
            reasons.append(f"authorization.ai_tool_policy is still unresolved ({policy.strip()!r}) — check the "
                           f"venue's AI-tool policy and record it")

    conf = _section(intake, "confidentiality", reasons)
    if conf:
        if conf.get("external_service_use") is not False:
            reasons.append("confidentiality.external_service_use must be false (external service use is never authorized by this skill)")
        if conf.get("data_reuse_planned") is not False:
            reasons.append("confidentiality.data_reuse_planned must be false (data reuse is never authorized by this skill)")
        if not is_filled(conf.get("retention_or_deletion_plan")):
            reasons.append("confidentiality.retention_or_deletion_plan is required (missing deletion/retention planning)")

    acc = _section(intake, "accountability", reasons)
    if acc:
        if not is_filled(acc.get("accountable_human")):
            reasons.append("accountability.accountable_human is required (missing human accountability)")
        if acc.get("conflicts_resolved") is not True:
            reasons.append("accountability.conflicts_resolved must be true (unresolved conflicts)")
        if not is_filled(acc.get("conflicts_of_interest")):
            reasons.append("accountability.conflicts_of_interest is required — state 'none' explicitly if there are none")

    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("intake", type=Path, help="Path to a completed review-intake JSON file")
    args = parser.parse_args()

    try:
        intake = json.loads(args.intake.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(intake, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    reasons = validate(intake)
    if reasons:
        print("BLOCKED: do not proceed with manuscript inspection.")
        for r in reasons:
            print(f"  - {r}")
        return 1

    print("READY_FOR_LOCAL_REVIEW")
    print("This confirms declarations are complete and no hard-blocking condition was found — it does not verify their truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
