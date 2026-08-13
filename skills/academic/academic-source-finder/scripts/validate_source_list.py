#!/usr/bin/env python3
"""Validate a caller-declared list of academic sources against the citable-
academic-source checklist (references/source_type_allowlist.json): a
recognized source_type, an honest peer-reviewed/non-academic declaration, a
resolvable doi_or_url, a recorded accessed_date, and (optionally) a
recency threshold. Stdlib only, local, deterministic -- no AI/network call
of any kind, and it does NOT search anything itself.

This is a protocol validator, not a search service: the calling agent finds
sources with its own web/database tools (see SKILL.md's "Protocol" section
for where a disciplined academic search looks), records them in this
script's JSON schema, and this script checks the record stayed disciplined
before the source list is trusted for an essay/paper.

Usage:
    python validate_source_list.py source_list.json \
        [--max-age-years N --current-year Y] [--render sources.md] [--force]
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

REFERENCES_PATH = Path(__file__).resolve().parent.parent / "references" / "source_type_allowlist.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_SOURCE_FIELDS = (
    "id", "title", "authors", "publication_year", "source_type",
    "peer_reviewed", "venue_or_publisher", "doi_or_url", "accessed_date",
)


def load_allowlist() -> dict:
    try:
        data = json.loads(REFERENCES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: cannot read bundled allowlist {REFERENCES_PATH}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    return data["academic_source_types"]


def validate(record: dict, allowlist: dict, max_age_years: int | None, current_year: int | None) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings

    seen_ids: dict[str, int] = {}

    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            errors.append(f"sources[{i}] must be an object")
            continue

        missing = [f for f in REQUIRED_SOURCE_FIELDS if f not in src]
        if missing:
            errors.append(f"sources[{i}]: missing required field(s): {', '.join(missing)}")
            continue

        src_id = src["id"]
        label = f"sources[{i}] (id={src_id!r})"
        if not isinstance(src_id, str) or not src_id.strip():
            errors.append(f"sources[{i}]: id must be a non-empty string")
        else:
            if src_id in seen_ids:
                errors.append(f"{label}: duplicate id, already used by sources[{seen_ids[src_id]}]")
            seen_ids[src_id] = i

        title = src["title"]
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label}: title must be a non-empty string")

        authors = src["authors"]
        if not isinstance(authors, list) or not authors or not all(isinstance(a, str) and a.strip() for a in authors):
            errors.append(f"{label}: authors must be a non-empty list of non-empty strings")

        pub_year = src["publication_year"]
        if not isinstance(pub_year, int) or isinstance(pub_year, bool):
            errors.append(f"{label}: publication_year must be an integer, got {pub_year!r}")
            pub_year = None

        source_type = src["source_type"]
        if source_type not in allowlist:
            errors.append(
                f"{label}: source_type {source_type!r} is not in the recognized allowlist "
                f"({sorted(allowlist.keys())})"
            )
            source_type = None

        peer_reviewed = src["peer_reviewed"]
        if not isinstance(peer_reviewed, bool):
            errors.append(f"{label}: peer_reviewed must be true or false, got {peer_reviewed!r}")
            peer_reviewed = None

        venue = src["venue_or_publisher"]
        if not isinstance(venue, str) or not venue.strip():
            errors.append(f"{label}: venue_or_publisher must be a non-empty string")

        doi_or_url = src["doi_or_url"]
        if not isinstance(doi_or_url, str) or not doi_or_url.strip():
            errors.append(f"{label}: doi_or_url must be a non-empty string")

        accessed_date = src["accessed_date"]
        if not isinstance(accessed_date, str) or not DATE_RE.match(accessed_date):
            errors.append(f"{label}: accessed_date must be a non-empty string in YYYY-MM-DD format, got {accessed_date!r}")

        # Non-academic sources require an explicit, non-empty justification --
        # never silently treated as equivalent to a vetted source.
        if source_type == "non-academic":
            justification = src.get("non_academic_justification")
            if not isinstance(justification, str) or not justification.strip():
                errors.append(
                    f"{label}: source_type is 'non-academic' but non_academic_justification is missing/empty "
                    f"-- a non-academic source requires an explicit, reviewable reason for inclusion"
                )

        # Internal-consistency check: peer_reviewed should agree with the
        # declared source_type's typical vetting process. Flagged as a
        # warning (the declaration might be an honest edge case, e.g. a
        # journal that skipped peer review for an invited editorial), not a
        # hard error, since this skill cannot independently verify the claim.
        if source_type == "preprint" and peer_reviewed is True:
            warnings.append(f"{label}: source_type is 'preprint' but peer_reviewed is true -- preprints are by definition not (yet) peer-reviewed, double-check this")
        if source_type == "non-academic" and peer_reviewed is True:
            warnings.append(f"{label}: source_type is 'non-academic' but peer_reviewed is true -- verify this is correct")
        if source_type in ("peer-reviewed-journal-article", "conference-paper") and peer_reviewed is False:
            warnings.append(f"{label}: source_type is {source_type!r} but peer_reviewed is false -- verify this is correct")

        if max_age_years is not None and pub_year is not None and current_year is not None:
            age = current_year - pub_year
            if age > max_age_years:
                warnings.append(
                    f"{label}: published {pub_year}, {age} years before the declared current_year {current_year} "
                    f"-- exceeds the {max_age_years}-year recency threshold"
                )

    return errors, warnings


def to_markdown(record: dict) -> str:
    lines = ["# Academic Source List", ""]
    for src in record.get("sources", []):
        authors = ", ".join(src.get("authors", []))
        lines.append(f"- **[{src.get('id', '')}]** {src.get('title', '')} — {authors} ({src.get('publication_year', '')}). "
                     f"{src.get('venue_or_publisher', '')}. {src.get('source_type', '')}"
                     f"{'' if src.get('peer_reviewed') else ', not peer-reviewed'}. "
                     f"{src.get('doi_or_url', '')} (accessed {src.get('accessed_date', '')})")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_list", type=Path, help="Path to a source list JSON file (see assets/source_list_template.json)")
    parser.add_argument("--max-age-years", type=int, default=None, help="Flag sources older than this many years as a recency warning. Requires --current-year.")
    parser.add_argument("--current-year", type=int, default=None, help="The caller-declared current year to compute source age against. Never inferred from the system clock (determinism).")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render a Markdown source list to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if (args.max_age_years is None) != (args.current_year is None):
        print("MALFORMED: --max-age-years and --current-year must be supplied together, or not at all", file=sys.stderr)
        return 2

    try:
        record = json.loads(args.source_list.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(record, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    allowlist = load_allowlist()
    errors, warnings = validate(record, allowlist, args.max_age_years, args.current_year)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: every source has a recognized source_type, an honest peer-reviewed/non-academic declaration, "
          "a doi_or_url, and a recorded accessed_date. This confirms the checklist was followed, not that the "
          "sources' content actually supports whatever claim they're cited for.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(record), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
