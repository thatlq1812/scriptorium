#!/usr/bin/env python3
"""Validate a hypothesis record JSON file against the structural requirements
in assets/hypothesis_record_template.json — stdlib only, local, deterministic,
non-scoring. This checks structural completeness and internal consistency
(e.g. every candidate stays labeled "candidate", every prediction references
a real candidate id and at least one rival). It does NOT judge whether any
hypothesis is correct, novel, or worth pursuing — that is human judgment.

Exit codes: 0 = structurally valid, 1 = validation errors found,
2 = malformed input (not valid JSON / not an object).

Usage:
    python validate_hypothesis_schema.py record.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CLAIM_TYPES = {"descriptive", "associational", "predictive", "causal", "mechanistic"}
CANDIDATE_CLASSES = {
    "mechanism", "measurement_artifact", "confounding", "selection_bias",
    "reverse_causation", "temporal_boundary_condition", "stochastic_variation",
    "competing_mechanism",
}
FORBIDDEN_STATUS_VALUES = {"confirmed", "true", "proven", "established", "fact"}


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    observation = record.get("observation")
    if not isinstance(observation, dict) or not observation.get("description"):
        errors.append("observation.description is required")

    if not record.get("research_question"):
        errors.append("research_question is required")

    claim_type = record.get("claim_type")
    if claim_type not in CLAIM_TYPES:
        errors.append(f"claim_type must be one of {sorted(CLAIM_TYPES)}, got {claim_type!r}")

    candidates = record.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
        candidates = []

    candidate_ids = set()
    for i, cand in enumerate(candidates):
        if not isinstance(cand, dict):
            errors.append(f"candidates[{i}] must be an object")
            continue
        cid = cand.get("id")
        if not cid:
            errors.append(f"candidates[{i}].id is required")
        else:
            if cid in candidate_ids:
                errors.append(f"duplicate candidate id: {cid}")
            candidate_ids.add(cid)
        if not cand.get("statement"):
            errors.append(f"candidates[{i}].statement is required")
        if cand.get("class") not in CANDIDATE_CLASSES:
            errors.append(f"candidates[{i}].class must be one of {sorted(CANDIDATE_CLASSES)}, got {cand.get('class')!r}")
        status = str(cand.get("status", "")).strip().lower()
        if status in FORBIDDEN_STATUS_VALUES:
            errors.append(
                f"candidates[{i}].status is {cand.get('status')!r} — a hypothesis is never marked "
                f"confirmed/true/proven/established/fact in this record; use 'candidate' and update "
                f"status narratively elsewhere once evidence accumulates"
            )
        elif status != "candidate":
            errors.append(f"candidates[{i}].status must be 'candidate', got {cand.get('status')!r}")

    if len(candidate_ids) < 2:
        errors.append(
            "fewer than 2 distinct candidates — hypothesis generation requires generating rivals, "
            "not a single explanation"
        )

    predictions = record.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        errors.append("predictions must be a non-empty list")
        predictions = []

    for i, pred in enumerate(predictions):
        if not isinstance(pred, dict):
            errors.append(f"predictions[{i}] must be an object")
            continue
        cid = pred.get("candidate_id")
        if cid not in candidate_ids:
            errors.append(f"predictions[{i}].candidate_id {cid!r} does not match any candidate id")
        for field in ("observable", "expected_pattern", "falsifying_result"):
            if not pred.get(field):
                errors.append(f"predictions[{i}].{field} is required")
        contrasted = pred.get("contrasted_with")
        if not isinstance(contrasted, list) or not contrasted:
            errors.append(f"predictions[{i}].contrasted_with must list at least one rival candidate id")
        else:
            for rival in contrasted:
                if rival not in candidate_ids:
                    errors.append(f"predictions[{i}].contrasted_with references unknown candidate id {rival!r}")

    authorization = record.get("authorization")
    if not isinstance(authorization, dict) or not authorization.get("accountable_human"):
        errors.append("authorization.accountable_human is required")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_hypothesis_schema.py record.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(record, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors = validate(record)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VALID: structurally complete. This confirms structure only, not scientific correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
