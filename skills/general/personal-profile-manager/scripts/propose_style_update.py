#!/usr/bin/env python3
"""Turn a feedback log into a PROPOSED instruction-update block.

Deliberately proposal-only -- never writes to CLAUDE.md/AGENTS.md or any
harness system prompt directly. The output is a Markdown block a human (or
the calling agent, after the human reviews it) manually inserts. This
mirrors document-ai-structurer's legal-article mode: a script proposes
candidate structure explicitly labeled unverified, a reviewing party
applies it -- never a script silently rewriting the instructions that
govern its own future behavior.

feedback_log.json shape: { "entries": [ { "date", "category", "feedback_text" }, ... ] }

Usage:
    python propose_style_update.py <feedback_log.json> [-o proposal.md]

Exit 0 = proposal generated, 1 = empty/no valid entries, 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_ENTRY_FIELDS = {"date", "category", "feedback_text"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feedback_log_path")
    parser.add_argument("-o", "--output", help="Write the proposal Markdown to this path")
    args = parser.parse_args()

    path = Path(args.feedback_log_path)
    if not path.exists():
        print(f"ERROR: feedback log not found: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "entries" not in data:
        print("ERROR: feedback log must be a JSON object with an 'entries' list.", file=sys.stderr)
        return 2

    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        print("ERROR: 'entries' must be a non-empty list.", file=sys.stderr)
        return 2

    by_category: dict[str, list[dict]] = defaultdict(list)
    malformed: list[str] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or not REQUIRED_ENTRY_FIELDS.issubset(entry):
            malformed.append(f"entry {i}: missing one of {sorted(REQUIRED_ENTRY_FIELDS)}")
            continue
        by_category[entry["category"]].append(entry)

    if malformed:
        print(f"ERROR: {len(malformed)} malformed entr(y/ies):", file=sys.stderr)
        for m in malformed:
            print(f"  - {m}", file=sys.stderr)
        return 2

    if not by_category:
        print("ERROR: no valid entries after parsing.", file=sys.stderr)
        return 1

    lines = [
        "> [!IMPORTANT]",
        "> PROPOSED instruction update, generated from `personal-profile-manager`'s feedback log.",
        "> Review before inserting into CLAUDE.md/AGENTS.md or a harness system prompt --",
        "> this text is NOT auto-applied anywhere.",
        "",
        "## Proposed writing-style / behavior adaptation",
        "",
    ]
    for category in sorted(by_category):
        lines.append(f"### {category}")
        for entry in by_category[category]:
            lines.append(f"- {entry['feedback_text']} (recorded {entry['date']})")
        lines.append("")

    proposal = "\n".join(lines)
    print(proposal)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(proposal, encoding="utf-8", newline="\n")
        print(f"\nWrote proposal to {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
