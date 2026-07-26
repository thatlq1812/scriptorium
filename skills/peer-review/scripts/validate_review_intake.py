#!/usr/bin/env python3
"""Validate a completed review-intake JSON file (see
assets/review_intake_template.json) against the mandatory authorization,
confidentiality, and accountability gate — stdlib only, local, deterministic.
This validates DECLARATIONS, not their truth: it cannot verify that the
named authorization is real, only that the required fields were filled in
and no hard-blocking condition (external service use, data reuse, unresolved
conflicts) is declared.

Prints READY_FOR_LOCAL_REVIEW (proceed) or BLOCKED (with reasons) — do not
proceed with any manuscript inspection while BLOCKED.

Exit codes: 0 = READY_FOR_LOCAL_REVIEW, 1 = BLOCKED, 2 = malformed input.

Usage:
    python validate_review_intake.py completed-intake.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_REVIEW_MODELS = {"single-blind", "double-blind", "open", "other"}


def validate(intake: dict) -> list[str]:
    reasons: list[str] = []

    if not intake.get("submission_type"):
        reasons.append("submission_type is required")
    if not intake.get("review_question"):
        reasons.append("review_question is required")
    if intake.get("review_model") not in VALID_REVIEW_MODELS:
        reasons.append(f"review_model must be one of {sorted(VALID_REVIEW_MODELS)}")

    auth = intake.get("authorization", {})
    if not isinstance(auth, dict) or not auth.get("authorized_by"):
        reasons.append("authorization.authorized_by is required (undocumented authorization)")
    if not isinstance(auth, dict) or not auth.get("authorization_basis"):
        reasons.append("authorization.authorization_basis is required")
    if not isinstance(auth, dict) or auth.get("venue_policy_checked") is not True:
        reasons.append("authorization.venue_policy_checked must be true (unchecked venue policy)")

    conf = intake.get("confidentiality", {})
    if not isinstance(conf, dict):
        reasons.append("confidentiality object is required")
    else:
        if conf.get("external_service_use") is not False:
            reasons.append("confidentiality.external_service_use must be false (external service use is never authorized by this skill)")
        if conf.get("data_reuse_planned") is not False:
            reasons.append("confidentiality.data_reuse_planned must be false (data reuse is never authorized by this skill)")
        if not conf.get("retention_or_deletion_plan"):
            reasons.append("confidentiality.retention_or_deletion_plan is required (missing deletion/retention planning)")

    acc = intake.get("accountability", {})
    if not isinstance(acc, dict) or not acc.get("accountable_human"):
        reasons.append("accountability.accountable_human is required (missing human accountability)")
    if not isinstance(acc, dict) or acc.get("conflicts_resolved") is not True:
        reasons.append("accountability.conflicts_resolved must be true (unresolved conflicts)")

    return reasons


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_review_intake.py completed-intake.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        intake = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
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
