#!/usr/bin/env python3
"""Scan a Markdown/text draft for overclaiming language — words that present
a hypothesis, correlation, or model output as established fact/causation
(e.g. "proves", "confirms", "X causes Y") — and flag each occurrence with a
hedged alternative. Stdlib only (re), local, deterministic. This is a
pattern-matching lint, not a semantic checker: it will miss paraphrased
overclaims and can flag legitimate uses — review every flag, don't blindly
auto-replace.

Fenced code blocks and blockquoted lines are skipped by default (quoting
someone else's overclaim to critique it is not the author overclaiming);
pass --include-quotes to scan them too. A line ending in `<!-- claim-ok -->`
is skipped, for a claim the author has deliberately justified.

Severities: high = clinical/absence claims, medium = proof/confirmation
language, low = weak causal phrasing that is often legitimate.

Exit codes: 0 = nothing at or above --fail-on, 1 = at least one flag at or
above it, 2 = file not found. Flags below the threshold are still printed.

Usage:
    python lint_causal_claims.py draft.md
    python lint_causal_claims.py draft.md --fail-on high
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}

# Hedged constructions are not overclaims: "may cause", "could confirm"...
HEDGE = r"(?<!\bmay )(?<!\bmight )(?<!\bcould )(?<!\bcan )(?<!\bwould )(?<!\bto )"

# (pattern, category, severity, suggested hedge)
PATTERNS: list[tuple[re.Pattern, str, str, str]] = [
    (re.compile(rf"{HEDGE}\bproves?\b", re.I), "overclaim", "medium", "use 'is consistent with' or 'supports'"),
    (re.compile(r"\bproven\b", re.I), "overclaim", "medium", "use 'supported by the evidence gathered so far'"),
    (re.compile(rf"{HEDGE}\bconfirms?\b", re.I), "overclaim", "medium", "use 'is consistent with' — a single study rarely confirms"),
    (re.compile(r"\bdemonstrates? that\b", re.I), "overclaim", "medium", "use 'suggests that' or 'is associated with'"),
    (re.compile(r"\bestablishes? that\b", re.I), "overclaim", "medium", "use 'proposes that' or 'suggests that'"),
    (re.compile(r"\b(definitively|conclusively|unequivocally)\b", re.I), "overclaim", "medium", "drop the intensifier and state the evidence and its limits"),
    (re.compile(rf"{HEDGE}\b(causes|caused|causing)\b", re.I), "causal-language", "medium", "state the design/estimand that justifies a causal claim, or use 'is associated with'"),
    (re.compile(r"\b(leads to|results in|drives|due to|because of)\b", re.I), "causal-language", "low", "verify a causal design justifies this; otherwise use 'is associated with' or 'coincides with'"),
    (re.compile(r"\bno prior work exists\b|\bnever been (studied|reported|shown)\b|\bfirst (study|work|paper) to\b", re.I),
     "absence-claim", "high", "use 'not located within the documented search boundary'"),
    (re.compile(r"\bdiagnos(is|e|ed|es)\b", re.I), "clinical-claim", "high",
     "this skill does not produce patient-specific diagnoses — route to a qualified clinician"),
    (re.compile(r"\bwill cure\b|\bcures\b|\bshould be (treated|prescribed) with\b", re.I), "clinical-claim", "high",
     "avoid definitive treatment/outcome claims outside an authorized clinical context"),
]

FENCE_RE = re.compile(r"^\s*(```|~~~)")
QUOTE_RE = re.compile(r"^\s*>")
SUPPRESS_RE = re.compile(r"<!--\s*claim-ok\s*-->\s*$")


def lint(text: str, include_quotes: bool = False) -> list[dict]:
    flags: list[dict] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not include_quotes and (in_fence or QUOTE_RE.match(line) or SUPPRESS_RE.search(line)):
            continue
        for pattern, category, severity, hedge in PATTERNS:
            for match in pattern.finditer(line):
                flags.append({
                    "line": lineno,
                    "category": category,
                    "severity": severity,
                    "matched": match.group(0),
                    "context": line.strip(),
                    "suggested_hedge": hedge,
                })
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", type=Path, help="Markdown/text draft to lint")
    parser.add_argument("--fail-on", choices=sorted(SEVERITY_ORDER, key=SEVERITY_ORDER.get), default="low",
                        help="Lowest severity that makes this exit 1 (default: low, i.e. any flag)")
    parser.add_argument("--include-quotes", action="store_true",
                        help="Also scan fenced code blocks and blockquoted lines")
    args = parser.parse_args()

    if not args.draft.is_file():
        print(f"FILE NOT FOUND: {args.draft}", file=sys.stderr)
        return 2

    try:
        text = args.draft.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"CANNOT READ: {exc}", file=sys.stderr)
        return 2

    flags = lint(text, args.include_quotes)
    if not flags:
        print("OK: no overclaiming patterns matched. This is a lint, not proof the draft is well-hedged.")
        return 0

    threshold = SEVERITY_ORDER[args.fail_on]
    blocking = [f for f in flags if SEVERITY_ORDER[f["severity"]] >= threshold]
    print(f"FLAGGED: {len(flags)} occurrence(s), {len(blocking)} at or above severity '{args.fail_on}' — "
          f"review each, this is a pattern match, not semantic understanding.")
    for f in sorted(flags, key=lambda f: (-SEVERITY_ORDER[f["severity"]], f["line"])):
        print(f"  line {f['line']} [{f['severity']}/{f['category']}] '{f['matched']}' — {f['suggested_hedge']}")
        print(f"    context: {f['context']}")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
