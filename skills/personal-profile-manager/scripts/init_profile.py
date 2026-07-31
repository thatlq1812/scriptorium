#!/usr/bin/env python3
"""Scaffold a local personal/profile.json from the bundled template.

Refuses to overwrite an existing profile without --force -- a profile holds
real PII (CCCD, tax ID, contact details), so silent overwrite would be a
real data-loss risk, not just an inconvenience.

--with-org-profile additionally merges the bundled org_profile_template.json's
"org_profile" section into the scaffolded file. This is an OPTIONAL section
distinct from the individual-person "organization" section already scaffolded
by default -- it represents the profile as an ISSUING ORGANIZATION (letterhead
identity: org name, parent org, abbreviation, locality, logo, departments,
signatory roles) rather than just one person's own org/contact details. Same
whole-file overwrite semantics as the base scaffold: this is not a merge into
an existing file, it is part of what gets written when the file is (re)created.

Usage:
    python init_profile.py <output_path> [--force] [--with-org-profile]

Exit 0 = created, 1 = already exists (no --force), 2 = bad arguments.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "profile_template.json"
ORG_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "org_profile_template.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_path", help="Where to write the new profile.json")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file")
    parser.add_argument(
        "--with-org-profile",
        action="store_true",
        help="Also include the optional org_profile (issuing-organization/letterhead) section",
    )
    args = parser.parse_args()

    out = Path(args.output_path)
    if out.exists() and not args.force:
        print(f"ERROR: {out} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    template_text = TEMPLATE.read_text(encoding="utf-8")
    # Round-trip through json to fail loudly if the bundled template itself is malformed.
    profile_data = json.loads(template_text)

    if args.with_org_profile:
        org_template_text = ORG_TEMPLATE.read_text(encoding="utf-8")
        org_data = json.loads(org_template_text)
        if not isinstance(org_data, dict) or "org_profile" not in org_data:
            print(
                f"ERROR: bundled {ORG_TEMPLATE} is malformed (missing 'org_profile' key).",
                file=sys.stderr,
            )
            return 2
        profile_data["org_profile"] = org_data["org_profile"]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(profile_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Created {out} from template. Edit it with your real details before use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
