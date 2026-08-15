#!/usr/bin/env python3
"""Lint a set of campaign links' UTM parameters against Google's own
official GA4 documentation on attribution -- lowercase/no-space parameter
values, a caller-declared "UTM playbook" of approved utm_source/utm_medium
values, required parameters present on every EXTERNAL link, and UTM
parameters absent from every INTERNAL link (tagging an internal link
overwrites the original session's source data). Stdlib only (json,
argparse, urllib.parse), local, deterministic -- no AI/network call.

SCOPE LIMIT (read before use): this checks UTM STRUCTURE/GOVERNANCE only --
it does not verify a link actually resolves, does not check the target
page's own content, and does not query GA4 itself. Grounded in Google's
own official documentation (support.google.com), not a 3rd-party blog --
see references/research_10_digital_marketing_regulations/research_brief.json
findings S4/S5.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_utm_links.py <links_record.json>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_UTM_PARAMS = ("utm_source", "utm_medium", "utm_campaign")
ALL_UTM_PARAMS = REQUIRED_UTM_PARAMS + ("utm_term", "utm_content")
SPACE_RE = re.compile(r"[ \t]|%20")


def extract_utm_params(url: str) -> dict[str, str]:
    """Return {param_name: raw_value} for every utm_* query param present
    (first value only if repeated -- a repeated utm param is itself a
    real, separately-flagged issue, not silently resolved here)."""
    query = urlparse(url).query
    parsed = parse_qs(query, keep_blank_values=True)
    return {k: v[0] for k, v in parsed.items() if k in ALL_UTM_PARAMS}


def validate_link(link: dict, playbook: dict | None, index: int) -> list[str]:
    errors: list[str] = []
    p = f"links[{index}]"

    url = link.get("url")
    if not isinstance(url, str) or not url.strip():
        return [f"{p}.url is required and must be non-empty text"]

    is_internal = link.get("is_internal")
    if not isinstance(is_internal, bool):
        errors.append(f"{p}.is_internal must be true or false, got {is_internal!r}")
        return errors  # can't apply the internal/external rule without knowing which

    try:
        params = extract_utm_params(url)
    except ValueError as exc:
        return [f"{p}.url could not be parsed: {exc}"]

    if is_internal:
        if params:
            errors.append(
                f"{p}: internal link carries UTM parameter(s) {sorted(params)} -- GA4's own official guidance "
                "is that UTMs should only be applied to external links; tagging an internal link overwrites "
                "the original session's source data and corrupts attribution"
            )
        return errors

    # External link from here on.
    for req in REQUIRED_UTM_PARAMS:
        if req not in params:
            errors.append(
                f"{p}: external link is missing required parameter '{req}' -- a session with no matching "
                "channel rule falls into GA4's 'Unassigned' default channel group"
            )

    for name, value in params.items():
        if value != value.lower():
            errors.append(f"{p}.{name}={value!r} is not all-lowercase -- GA4 treats UTM values as case-sensitive, fragmenting reporting")
        if SPACE_RE.search(value):
            errors.append(f"{p}.{name}={value!r} contains a space -- use underscores or hyphens instead")

    if playbook is not None:
        approved_sources = playbook.get("approved_sources")
        approved_mediums = playbook.get("approved_mediums")
        source = params.get("utm_source")
        medium = params.get("utm_medium")
        if source is not None and isinstance(approved_sources, list) and source not in approved_sources:
            errors.append(f"{p}.utm_source={source!r} is not in the declared utm_playbook.approved_sources {approved_sources}")
        if medium is not None and isinstance(approved_mediums, list) and medium not in approved_mediums:
            errors.append(f"{p}.utm_medium={medium!r} is not in the declared utm_playbook.approved_mediums {approved_mediums}")

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    playbook = record.get("utm_playbook")
    if playbook is not None and not isinstance(playbook, dict):
        errors.append("utm_playbook must be an object if present")
        playbook = None

    links = record.get("links")
    if not isinstance(links, list) or not links:
        return errors + ["links must be a non-empty list"]

    for i, link in enumerate(links):
        if not isinstance(link, dict):
            errors.append(f"links[{i}] must be an object")
            continue
        errors.extend(validate_link(link, playbook, i))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a links-record JSON file (see assets/links_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "links" not in data:
        print("MALFORMED: input must be a JSON object with a 'links' key", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks UTM parameter STRUCTURE/GOVERNANCE per GA4's own official documentation "
        "(lowercase, no spaces, required params on external links, no UTM params on internal links, "
        "optional approved-value playbook) -- it does not verify the link resolves or query GA4 itself.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(data.get('links', []))} link(s), no UTM governance issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
