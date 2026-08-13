#!/usr/bin/env python3
"""Validate a claim-evidence matrix CSV (see
assets/claim_evidence_matrix_template.csv) — stdlib only (csv), local,
deterministic. Reports IDs and counts only; it deliberately never prints the
`claim_text` or `location` column content back, so this report is safe to
share/paste even though the underlying matrix file itself may contain
confidential manuscript-derived notes.

Checks: every row has a unique claim_id, a location, and evidence_ids OR an
explicit alignment_ok=false with a limitation_noted; every alignment_ok=false
row has a non-empty requested_action.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_claim_evidence.py local-claim-matrix.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_COLUMNS = {"claim_id", "location", "evidence_ids", "alignment_ok", "limitation_noted", "requested_action"}


def _parse_bool(value: str) -> bool | None:
    v = (value or "").strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None


def validate(rows: list[dict]) -> tuple[list[str], dict]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    aligned = 0
    misaligned = 0

    counted = 0
    for i, row in enumerate(rows, start=1):
        if not any((value or "").strip() for key, value in row.items() if isinstance(key, str)):
            continue  # blank line at the end of the file, not a claim
        counted += 1
        if None in row:
            errors.append(f"row {i}: more fields than the header declares (unquoted comma or stray delimiter)")
        claim_id = (row.get("claim_id") or "").strip()
        if not claim_id:
            errors.append(f"row {i}: claim_id is required")
            continue
        if claim_id in seen_ids:
            errors.append(f"row {i}: duplicate claim_id '{claim_id}'")
        seen_ids.add(claim_id)

        if not (row.get("location") or "").strip():
            errors.append(f"claim {claim_id}: location is required")

        aligned_flag = _parse_bool(row.get("alignment_ok", ""))
        if aligned_flag is None:
            errors.append(f"claim {claim_id}: alignment_ok must be true/false")
            continue

        if aligned_flag:
            aligned += 1
            if not (row.get("evidence_ids") or "").strip():
                errors.append(f"claim {claim_id}: alignment_ok=true but evidence_ids is empty")
        else:
            misaligned += 1
            if not (row.get("limitation_noted") or "").strip():
                errors.append(f"claim {claim_id}: alignment_ok=false requires limitation_noted")
            if not (row.get("requested_action") or "").strip():
                errors.append(f"claim {claim_id}: alignment_ok=false requires requested_action")

    summary = {"total_claims": counted, "aligned": aligned, "misaligned": misaligned}
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("matrix", type=Path, help="Path to a claim-evidence matrix CSV")
    args = parser.parse_args()

    if not args.matrix.is_file():
        print(f"MALFORMED: file not found: {args.matrix}", file=sys.stderr)
        return 2

    try:
        with args.matrix.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
                print(f"MALFORMED: CSV must have columns {sorted(REQUIRED_COLUMNS)}", file=sys.stderr)
                return 2
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"MALFORMED: cannot read the matrix ({exc})", file=sys.stderr)
        return 2

    errors, summary = validate(rows)

    print(f"Claims scanned: {summary['total_claims']} (aligned: {summary['aligned']}, misaligned: {summary['misaligned']})")
    if errors:
        print(f"INVALID: {len(errors)} error(s) — referenced by claim_id only, not by content:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: matrix is structurally complete. This does not verify that any claim is actually supported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
