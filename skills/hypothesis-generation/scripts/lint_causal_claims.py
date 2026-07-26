#!/usr/bin/env python3
"""Scan a Markdown/text draft for overclaiming language — words that present
a hypothesis, correlation, or model output as established fact/causation
(e.g. "proves", "confirms", "X causes Y") — and flag each occurrence with a
hedged alternative. Stdlib only (re), local, deterministic. This is a
pattern-matching lint, not a semantic checker: it will miss paraphrased
overclaims and can flag legitimate uses (e.g. quoting someone else's overclaim
to critique it) — review every flag, don't blindly auto-replace.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = file not found.

Usage:
    python lint_causal_claims.py draft.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# (pattern, category, suggested hedge)
PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bproves?\b", re.I), "overclaim", "use 'is consistent with' or 'supports'"),
    (re.compile(r"\bproven\b", re.I), "overclaim", "use 'supported by the evidence gathered so far'"),
    (re.compile(r"\bconfirms?\b", re.I), "overclaim", "use 'is consistent with' — a single study rarely confirms"),
    (re.compile(r"\bdemonstrates? that\b", re.I), "overclaim", "use 'suggests that' or 'is associated with'"),
    (re.compile(r"\bestablishes? that\b", re.I), "overclaim", "use 'proposes that' or 'suggests that'"),
    (re.compile(r"\b\w+ causes? \w+", re.I), "causal-language", "state the design/estimand that justifies a causal claim, or use 'is associated with'"),
    (re.compile(r"\bdue to\b", re.I), "causal-language", "verify a causal design justifies this; otherwise use 'associated with' or 'coincides with'"),
    (re.compile(r"\bno prior work exists\b", re.I), "absence-claim", "use 'not located within the documented search boundary'"),
    (re.compile(r"\bdiagnos(is|e|ed|es)\b", re.I), "clinical-claim", "this skill does not produce patient-specific diagnoses — route to a qualified clinician"),
    (re.compile(r"\bwill cure\b|\bcures\b", re.I), "clinical-claim", "avoid definitive treatment/outcome claims outside an authorized clinical context"),
]


def lint(text: str) -> list[dict]:
    flags = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, category, hedge in PATTERNS:
            for match in pattern.finditer(line):
                flags.append({
                    "line": lineno,
                    "category": category,
                    "matched": match.group(0),
                    "context": line.strip(),
                    "suggested_hedge": hedge,
                })
    return flags


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python lint_causal_claims.py draft.md", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"FILE NOT FOUND: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    flags = lint(text)

    if not flags:
        print("OK: no overclaiming patterns matched. This is a lint, not proof the draft is well-hedged.")
        return 0

    print(f"FLAGGED: {len(flags)} occurrence(s) — review each, this is a pattern match, not semantic understanding.")
    for f in flags:
        print(f"  line {f['line']} [{f['category']}] '{f['matched']}' — {f['suggested_hedge']}")
        print(f"    context: {f['context']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
