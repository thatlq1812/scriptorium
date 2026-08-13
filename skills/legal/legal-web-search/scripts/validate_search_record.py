#!/usr/bin/env python3
"""Validate a legal-web-search record: every result's URL must resolve to
an allowlisted domain (references/allowed_domains.json), every result must
carry an accessed_date, any reported hiệu lực-like status must be recorded
as "what the page displayed" (a structured object), never a bare asserted
fact, and a contradiction between 2 results reporting different status for
the same document must be explicitly addressed, not silently left
unresolved.

This script does NOT search anything itself and does NOT decide what a
document's real legal status is -- it only checks that a search record
someone (the calling agent, using its own web-search/fetch tools) already
produced is honestly scoped and self-consistent. Same discipline as
deep-research/legal-research-brief, applied to the search step specifically
because item 2 of the original practitioner survey explicitly flagged
hiệu-lực tracking as hard and this project has no free official API for it
-- the honest response is disciplined, disclosed sourcing, not a lookup
service pretending to have ground truth.

Short-term mitigation for JS-rendered sites (2026-07-27, owner decision after
a real attempt against dichvucong.gov.vn found its procedure/form pages
return only a JS shell to a direct fetch): a result may set
"js_shell_detected": true and skip a literal as_displayed_status quote, but
must then carry a non-empty "snippet_note" explaining what was actually
obtained (typically a WebSearch summary, not the page's literal text) --
never silently presented as if it were a direct-quote result. Long-term fix
(browser automation to render the DOM before parsing) is tracked as a
backlog item, not built here.

Stdlib only (json, argparse, re, urllib.parse) -- no network call.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_search_record.py <record.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ALLOWLIST_PATH = Path(__file__).resolve().parents[1] / "references" / "allowed_domains.json"


def load_allowlist() -> dict[str, str]:
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {d["domain"]: d["tier"] for d in data["domains"]}


def domain_tier(url: str, allowlist: dict[str, str]) -> str | None:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return None
    for domain, tier in allowlist.items():
        if host == domain or host.endswith("." + domain):
            return tier
    return None


def validate(record: dict, allowlist: dict[str, str]) -> list[str]:
    errors: list[str] = []

    if not record.get("query"):
        errors.append("query is required")
    if not record.get("search_date"):
        errors.append("search_date is required")

    if record.get("caveat_acknowledged") is not True:
        errors.append(
            "caveat_acknowledged must be exactly true -- confirms whoever ran this search read that "
            "no result here is a hiệu lực (in-effect) determination, only what a source page displayed"
        )

    if not record.get("contradiction_notes"):
        errors.append("contradiction_notes is required (state 'none identified' explicitly if that's honest -- don't omit)")

    results = record.get("results")
    if not isinstance(results, list) or not results:
        errors.append("results must be a non-empty list")
        return errors

    status_by_ref: dict[str, set[str]] = {}
    for i, r in enumerate(results):
        if not isinstance(r, dict):
            errors.append(f"results[{i}] must be an object")
            continue
        for field in ("url", "title", "accessed_date"):
            if not r.get(field):
                errors.append(f"results[{i}]: {field} is required")

        url = r.get("url")
        if url:
            tier = domain_tier(url, allowlist)
            if tier is None:
                errors.append(
                    f"results[{i}]: {url!r} is not on an allowlisted domain "
                    f"(see references/allowed_domains.json) -- add it there deliberately if it's a real "
                    f"official/reputable source, don't just accept whatever a search engine returned"
                )

        if r.get("js_shell_detected") is True and not r.get("snippet_note"):
            errors.append(
                f"results[{i}]: js_shell_detected is true but snippet_note is missing/empty -- when a direct "
                f"fetch only returned a JS-rendered shell (see legal-web-search's known limitation for "
                f"dichvucong.gov.vn), the result may still be recorded from a WebSearch snippet instead, but "
                f"must say explicitly what was actually obtained and how (short-term mitigation, not a literal "
                f"page quote)"
            )

        status = r.get("as_displayed_status")
        if status is not None:
            if not isinstance(status, dict) or not status.get("text"):
                errors.append(
                    f"results[{i}]: as_displayed_status must be an object with a non-empty 'text' field "
                    f"(what the source page literally displayed) -- never a bare status string"
                )
            else:
                ref = r.get("document_ref")
                if ref:
                    status_by_ref.setdefault(ref, set()).add(status["text"])

    for ref, texts in status_by_ref.items():
        if len(texts) > 1:
            notes = record.get("contradiction_notes", "")
            if ref not in notes:
                errors.append(
                    f"results disagree on displayed status for document_ref {ref!r} ({sorted(texts)}) "
                    f"but contradiction_notes doesn't mention {ref!r} -- a disagreement between sources "
                    f"must be surfaced explicitly, not silently left for whichever result came first"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a search record JSON file (see assets/search_record_template.json)")
    args = parser.parse_args()

    if not args.record.exists():
        print(f"Input not found: {args.record}", file=sys.stderr)
        return 1

    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(record, dict):
        print("MALFORMED: top-level record JSON must be an object", file=sys.stderr)
        return 2

    allowlist = load_allowlist()
    errors = validate(record, allowlist)

    print(
        "NOTE: this validates search-record discipline (allowlisted domains, dated access, disclosed-not-"
        "asserted status, contradictions surfaced) only -- it is NOT a hiệu lực (in-effect) determination "
        "and does not verify a document's real-world legal status. See legal-citation-checker for the same "
        "scope limit applied to citations.",
        file=sys.stderr,
    )

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"VALID: {len(record['results'])} result(s), all on allowlisted domains, dated, self-consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
