#!/usr/bin/env python3
"""Validate a personal/profile.json against the required schema.

Required top-level sections: identity, organization, contact -- each a flat
object of string values. Refuses loudly (never silently accepts a partial
profile) so a later autofill run doesn't silently propagate missing data
into a real document.

org_profile is an OPTIONAL top-level section (only validated if present) --
distinct from the individual-person "organization" section: it represents
the profile as an ISSUING ORGANIZATION for letterhead-style document
generation (org name, parent org, abbreviation, locality, logo, a department
list, and a signatory-title list). Cross-field checks enforced when present:
no duplicate department ids, no duplicate signatory ids/codes, and every
signatory's department_id (if set) must reference a department id that
actually exists in the declared department list (a dangling-reference check).

Usage:
    python validate_profile.py <profile.json>

Exit 0 = valid, 1 = structural violations found (all printed), 2 = malformed JSON / missing file.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_SECTIONS = {
    "identity": {"full_name"},
    "organization": {"org_name"},
    "contact": {"email"},
}

# org_profile.abbreviation / org_profile.departments[].abbreviation: 2-16
# upper-case Latin letters, plus the single Vietnamese letter "Đ" -- the only
# diacritic present in NĐ 30/2020 Phụ lục III's real viết-tắt examples (e.g.
# "QĐ", "HĐ"). Ported from the real production validator this section is
# grounded in (D:/elix/archive/platform_archive/modules/document/v6/co_quan_profile/schemas.py
# _VIET_TAT_PATTERN) -- mixed-case/accented forms break Số/ký hiệu rendering.
ORG_ABBREVIATION_PATTERN = re.compile(r"^[A-ZĐ]{2,16}$")

# org_profile.signatory_roles[].code: snake_case, 2-32 chars, starts with a
# lowercase letter -- same shape as the source's _CHUC_DANH_CODE_PATTERN.
SIGNATORY_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,31}$")

# org_profile.signatory_roles[].default_signing_authority: the 5 real
# quyền-hạn prefixes NĐ 30/2020 Mục IV.7 recognises, rendered literally on
# the document at ô 7a (TM. = thay mặt/on behalf of, KT. = ký thay/signed
# for, TL. = thừa lệnh/by order of, TUQ. = thừa uỷ quyền/by authorization,
# Q. = quyền/acting), plus "none" (signer signs in their own right, no
# prefix). Deliberately REQUIRED here (never defaulted to "none" the way the
# source schema does) -- this skill's "never silently fabricate/default a
# value" discipline means a signatory entry must state its authority
# explicitly, even if that explicit value is "none".
SIGNING_AUTHORITY_VALUES = {"none", "TM.", "KT.", "TL.", "TUQ.", "Q."}


def _validate_org_profile(org_profile: Any) -> list[str]:
    """Validate the optional org_profile section. Returns a list of error strings.

    Mirrors the real cross-field invariants from the production co_quan_profile
    schema this section is ported from: required identity fields, abbreviation
    format, no duplicate department ids, no duplicate signatory ids/codes, and
    every signatory's department_id (if set) must resolve to a real department.
    """
    errors: list[str] = []

    if not isinstance(org_profile, dict):
        return [f"section 'org_profile' must be an object, got {type(org_profile).__name__}"]

    # Required scalar fields.
    for field in ("name", "abbreviation", "locality"):
        value = org_profile.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"org_profile: required field '{field}' is missing or empty")

    abbreviation = org_profile.get("abbreviation")
    if isinstance(abbreviation, str) and abbreviation.strip():
        if not ORG_ABBREVIATION_PATTERN.match(abbreviation):
            errors.append(
                "org_profile.abbreviation: must be 2-16 upper-case Latin letters "
                f"(Đ accepted), got {abbreviation!r}"
            )

    departments = org_profile.get("departments", [])
    if not isinstance(departments, list):
        errors.append(f"org_profile.departments must be a list, got {type(departments).__name__}")
        departments = []

    department_ids: list[str] = []
    for i, dept in enumerate(departments):
        if not isinstance(dept, dict):
            errors.append(f"org_profile.departments[{i}]: must be an object, got {type(dept).__name__}")
            continue
        dept_id = dept.get("id")
        if not isinstance(dept_id, str) or not dept_id.strip():
            errors.append(f"org_profile.departments[{i}]: required field 'id' is missing or empty")
        else:
            department_ids.append(dept_id)
        for field in ("name", "abbreviation"):
            value = dept.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"org_profile.departments[{i}]: required field '{field}' is missing or empty")
        dept_abbr = dept.get("abbreviation")
        if isinstance(dept_abbr, str) and dept_abbr.strip():
            if not ORG_ABBREVIATION_PATTERN.match(dept_abbr):
                errors.append(
                    f"org_profile.departments[{i}].abbreviation: must be 2-16 upper-case "
                    f"Latin letters (Đ accepted), got {dept_abbr!r}"
                )

    if len(department_ids) != len(set(department_ids)):
        dupes = sorted({d for d in department_ids if department_ids.count(d) > 1})
        errors.append(f"org_profile.departments: duplicate department id(s): {dupes}")

    department_id_set = set(department_ids)

    signatory_roles = org_profile.get("signatory_roles", [])
    if not isinstance(signatory_roles, list):
        errors.append(f"org_profile.signatory_roles must be a list, got {type(signatory_roles).__name__}")
        signatory_roles = []

    signatory_ids: list[str] = []
    signatory_codes: list[str] = []
    for i, sig in enumerate(signatory_roles):
        if not isinstance(sig, dict):
            errors.append(f"org_profile.signatory_roles[{i}]: must be an object, got {type(sig).__name__}")
            continue
        sig_id = sig.get("id")
        if not isinstance(sig_id, str) or not sig_id.strip():
            errors.append(f"org_profile.signatory_roles[{i}]: required field 'id' is missing or empty")
        else:
            signatory_ids.append(sig_id)
        for field in ("label_full", "label_short"):
            value = sig.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"org_profile.signatory_roles[{i}]: required field '{field}' is missing or empty")

        code = sig.get("code")
        if not isinstance(code, str) or not code.strip():
            errors.append(f"org_profile.signatory_roles[{i}]: required field 'code' is missing or empty")
        else:
            signatory_codes.append(code)
            if not SIGNATORY_CODE_PATTERN.match(code):
                errors.append(
                    f"org_profile.signatory_roles[{i}].code: must be snake_case, 2-32 chars, "
                    f"starting with a lowercase letter, got {code!r}"
                )

        # default_signing_authority is REQUIRED and must be one of the 5 real
        # quyền-hạn prefixes (or "none") -- never silently defaulted.
        authority = sig.get("default_signing_authority")
        if authority is None or (isinstance(authority, str) and not authority.strip()):
            errors.append(
                f"org_profile.signatory_roles[{i}]: required field 'default_signing_authority' "
                "is missing -- must be explicitly one of "
                f"{sorted(SIGNING_AUTHORITY_VALUES)}"
            )
        elif not isinstance(authority, str) or authority not in SIGNING_AUTHORITY_VALUES:
            errors.append(
                f"org_profile.signatory_roles[{i}].default_signing_authority: {authority!r} "
                f"is not one of {sorted(SIGNING_AUTHORITY_VALUES)}"
            )

        dept_ref = sig.get("department_id")
        if dept_ref is not None:
            if not isinstance(dept_ref, str) or not dept_ref.strip():
                errors.append(
                    f"org_profile.signatory_roles[{i}].department_id: must be a non-empty "
                    f"string or null, got {dept_ref!r}"
                )
            elif dept_ref not in department_id_set:
                errors.append(
                    f"org_profile.signatory_roles[{i}] (id={sig.get('id')!r}): department_id "
                    f"{dept_ref!r} does not reference an existing entry in org_profile.departments"
                )

    if len(signatory_ids) != len(set(signatory_ids)):
        dupes = sorted({s for s in signatory_ids if signatory_ids.count(s) > 1})
        errors.append(f"org_profile.signatory_roles: duplicate signatory id(s): {dupes}")

    if len(signatory_codes) != len(set(signatory_codes)):
        dupes = sorted({c for c in signatory_codes if signatory_codes.count(c) > 1})
        errors.append(f"org_profile.signatory_roles: duplicate signatory code(s): {dupes}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_profile.py <profile.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: profile file not found: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("ERROR: profile.json must be a JSON object at the top level.", file=sys.stderr)
        return 2

    errors: list[str] = []
    for section, required_fields in REQUIRED_SECTIONS.items():
        if section not in data:
            errors.append(f"missing required section: '{section}'")
            continue
        section_value = data[section]
        if not isinstance(section_value, dict):
            errors.append(f"section '{section}' must be an object, got {type(section_value).__name__}")
            continue
        for field in required_fields:
            value = section_value.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"section '{section}': required field '{field}' is missing or empty")

    if "org_profile" in data:
        errors.extend(_validate_org_profile(data["org_profile"]))

    if errors:
        print(f"INVALID ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VALID: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
