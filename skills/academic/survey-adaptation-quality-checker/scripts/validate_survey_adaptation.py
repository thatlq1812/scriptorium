#!/usr/bin/env python3
"""Check a caller-declared survey/questionnaire translation-and-adaptation
process record against the real, peer-reviewed TRAPD methodology
(Translation, Review, Adjudication, Pretest, Documentation) plus the
back-translation cross-check convention. Stdlib only (json, argparse),
local, deterministic -- no AI/network call of any kind.

SCOPE LIMIT (read before use): this checks PROCESS-DOCUMENTATION
completeness only -- it does not and cannot judge whether the actual
translation is linguistically accurate (that requires real bilingual
subject-matter expertise this script does not have), only whether the
required process steps were performed and documented.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_survey_adaptation.py <adaptation_record.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

TRANSLATOR_ROLES = {"survey_methodologist", "translator", "subject_matter_expert"}


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def validate_translators(translators: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(translators, list) or len(translators) < 2:
        return [
            "translators must be a list of at least 2 independent translators -- TRAPD requires multiple "
            "translators, not a single person's forward translation"
        ]
    roles_seen: set[str] = set()
    for i, t in enumerate(translators):
        if not isinstance(t, dict):
            errors.append(f"translators[{i}] must be an object")
            continue
        require_nonempty_text(t.get("name"), f"translators[{i}].name", errors)
        role = t.get("expertise")
        if role not in TRANSLATOR_ROLES:
            errors.append(f"translators[{i}].expertise must be one of {sorted(TRANSLATOR_ROLES)}, got {role!r}")
        else:
            roles_seen.add(role)
    if len(translators) >= 2 and len(roles_seen) < 2:
        errors.append(
            f"translators collectively declare only {len(roles_seen)} distinct expertise type(s) "
            f"({sorted(roles_seen)}) -- TRAPD calls for varied expertise (survey methodology, translation, "
            "subject matter), not multiple people with the same single skill set"
        )
    return errors


def validate_review_adjudication(record: dict) -> list[str]:
    errors: list[str] = []
    if record.get("review_step_completed") is not True:
        errors.append("review_step_completed must be true -- TRAPD's Review step (translators discuss/reconcile independent versions) is required")
    require_nonempty_text(record.get("adjudication_notes"), "adjudication_notes (TRAPD's Adjudication step -- how disagreements between translators were resolved)", errors)
    return errors


def validate_back_translation(bt: object) -> list[str]:
    errors: list[str] = []
    if bt is None:
        return ["back_translation key is required (use back_translation: {\"performed\": false, \"reason\": \"...\"} if genuinely skipped, with a stated reason -- do not omit the key)"]
    if not isinstance(bt, dict):
        return ["back_translation must be an object"]

    if bt.get("performed") is not True:
        require_nonempty_text(bt.get("reason"), "back_translation.reason (required when back_translation.performed is false -- state why it was skipped)", errors)
        return errors

    require_nonempty_text(bt.get("back_translator_name"), "back_translation.back_translator_name", errors)
    require_nonempty_text(bt.get("comparison_notes"), "back_translation.comparison_notes (how the back-translated version was compared against the true original)", errors)
    return errors


def validate_pretest(pretest: object) -> list[str]:
    errors: list[str] = []
    if pretest is None:
        return ["pretest key is required (use pretest: {\"performed\": false, \"reason\": \"...\"} if genuinely skipped, with a stated reason -- do not omit the key)"]
    if not isinstance(pretest, dict):
        return ["pretest must be an object"]

    if pretest.get("performed") is not True:
        require_nonempty_text(pretest.get("reason"), "pretest.reason (required when pretest.performed is false -- state why it was skipped)", errors)
        return errors

    sample_size = pretest.get("sample_size")
    if not isinstance(sample_size, int) or isinstance(sample_size, bool) or sample_size < 1:
        errors.append(f"pretest.sample_size must be a positive integer when pretest.performed is true, got {sample_size!r}")
    require_nonempty_text(pretest.get("findings"), "pretest.findings", errors)
    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    if "translators" not in record:
        errors.append("translators key is required")
    else:
        errors.extend(validate_translators(record.get("translators")))

    errors.extend(validate_review_adjudication(record))
    errors.extend(validate_back_translation(record.get("back_translation") if "back_translation" in record else None))
    errors.extend(validate_pretest(record.get("pretest") if "pretest" in record else None))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a survey-adaptation-process JSON file (see assets/adaptation_record_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks PROCESS-DOCUMENTATION completeness against the TRAPD methodology (Translation/"
        "Review/Adjudication/Pretest/Documentation) plus back-translation -- it does not and cannot judge "
        "whether the actual translation is linguistically accurate, only whether the required steps were "
        "performed and documented.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: survey-adaptation process documentation is complete per TRAPD, no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
