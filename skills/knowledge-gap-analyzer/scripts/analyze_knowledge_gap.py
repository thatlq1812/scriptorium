#!/usr/bin/env python3
"""Flag required-for-target-role skills whose caller-declared self-assessed
confidence is below a caller-declared threshold.

Both the self-assessment (skill x confidence pairs) and the target-role
requirement list are always caller-supplied input -- this script never
invents a confidence value, a skill name, or a scoring methodology. The
confidence scale (1-5) is a plain caller-defined ordinal scale; this script
only compares the caller's own numbers against the caller's own threshold,
it does not interpret what "confidence 3" is supposed to mean.

A required skill that never appears in the self-assessment at all is
treated as a gap too (most conservative correct reading -- "never
assessed" is not evidence of "meets the bar"), and is reported distinctly
from "assessed but below threshold" so the two cases aren't conflated.

Stdlib only (json, argparse), local, deterministic, no AI/network calls.

Usage:
    python analyze_knowledge_gap.py self_assessment.json target_requirements.json \
        --threshold 3 [--output report.md] [--json]

Exit 0 = every required skill is self-assessed at/above --threshold.
Exit 1 = well-formed input but at least one required skill is below
         threshold or was never self-assessed -- gaps are flagged, not a
         crash.
Exit 2 = malformed input (bad JSON, missing/invalid fields, duplicate
         skill names, out-of-range confidence, out-of-range --threshold).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

MIN_CONFIDENCE, MAX_CONFIDENCE = 1, 5


class AnalyzerError(Exception):
    """Malformed input -- exit 2."""


def _norm(name: str) -> str:
    return " ".join(name.strip().lower().split())


def load_self_assessment(path: Path) -> dict[str, dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalyzerError(f"cannot read self-assessment file: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalyzerError("self-assessment file must contain a JSON object")

    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        raise AnalyzerError("'skills' must be a non-empty list")

    by_norm_name: dict[str, dict] = {}
    for i, s in enumerate(skills):
        if not isinstance(s, dict) or not s.get("name"):
            raise AnalyzerError(f"skills[{i}] must be an object with a non-empty 'name'")
        name = str(s["name"]).strip()
        key = _norm(name)
        if key in by_norm_name:
            raise AnalyzerError(f"duplicate skill in self-assessment: {name!r}")
        confidence = s.get("confidence")
        if not isinstance(confidence, int) or isinstance(confidence, bool) or not (MIN_CONFIDENCE <= confidence <= MAX_CONFIDENCE):
            raise AnalyzerError(
                f"skills[{i}] ({name!r}) confidence must be an integer {MIN_CONFIDENCE}-{MAX_CONFIDENCE}, got {confidence!r}"
            )
        by_norm_name[key] = {"name": name, "confidence": confidence}

    return by_norm_name


def load_target_requirements(path: Path) -> tuple[str, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalyzerError(f"cannot read target-requirements file: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalyzerError("target-requirements file must contain a JSON object")

    target_role = data.get("target_role")
    if not isinstance(target_role, str) or not target_role.strip():
        raise AnalyzerError("'target_role' must be a non-empty string")

    required = data.get("required_skills")
    if not isinstance(required, list) or not required:
        raise AnalyzerError("'required_skills' must be a non-empty list")

    seen: set[str] = set()
    normalized: list[str] = []
    for i, r in enumerate(required):
        if not isinstance(r, str) or not r.strip():
            raise AnalyzerError(f"required_skills[{i}] must be a non-empty string")
        name = r.strip()
        key = _norm(name)
        if key in seen:
            raise AnalyzerError(f"duplicate required_skills entry: {name!r}")
        seen.add(key)
        normalized.append(name)

    return target_role.strip(), normalized


def analyze(self_assessment: dict[str, dict], required_skills: list[str], threshold: int) -> dict:
    below_threshold = []
    not_assessed = []
    meets_bar = []

    for name in required_skills:
        key = _norm(name)
        entry = self_assessment.get(key)
        if entry is None:
            not_assessed.append(name)
        elif entry["confidence"] < threshold:
            below_threshold.append({"name": name, "confidence": entry["confidence"]})
        else:
            meets_bar.append({"name": name, "confidence": entry["confidence"]})

    gaps = len(below_threshold) + len(not_assessed)
    return {
        "threshold": threshold,
        "meets_bar": meets_bar,
        "below_threshold": below_threshold,
        "not_assessed": not_assessed,
        "gap_count": gaps,
        "ready": gaps == 0,
    }


def to_markdown(target_role: str, result: dict) -> str:
    status = "NO GAPS" if result["ready"] else f"{result['gap_count']} GAP(S) FOUND"
    lines = [
        f"# Knowledge gap report -- {target_role}",
        "",
        f"Confidence threshold required: {result['threshold']}",
        f"Status: {status}",
        "",
        "## Meets bar",
    ]
    if result["meets_bar"]:
        for s in result["meets_bar"]:
            lines.append(f"- {s['name']} (confidence {s['confidence']})")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Below threshold")
    if result["below_threshold"]:
        for s in result["below_threshold"]:
            lines.append(f"- [ ] {s['name']} (confidence {s['confidence']}, needs >= {result['threshold']})")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Never self-assessed")
    if result["not_assessed"]:
        for name in result["not_assessed"]:
            lines.append(f"- [ ] {name} (no self-assessment entry found)")
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("self_assessment", type=Path, help="Path to a self-assessment JSON file (see assets/self_assessment_template.json)")
    parser.add_argument("target_requirements", type=Path, help="Path to a target-requirements JSON file (see assets/target_requirements_template.json)")
    parser.add_argument("--threshold", type=int, required=True, help=f"Minimum confidence ({MIN_CONFIDENCE}-{MAX_CONFIDENCE}) required for a skill to count as met")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print raw JSON report instead of Markdown")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not (MIN_CONFIDENCE <= args.threshold <= MAX_CONFIDENCE):
        print(f"REFUSED: --threshold must be an integer {MIN_CONFIDENCE}-{MAX_CONFIDENCE}", file=sys.stderr)
        return 2

    try:
        self_assessment = load_self_assessment(args.self_assessment)
        target_role, required_skills = load_target_requirements(args.target_requirements)
    except AnalyzerError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    result = analyze(self_assessment, required_skills, args.threshold)

    output_text = (
        json.dumps({"target_role": target_role, **result}, indent=2, ensure_ascii=False)
        if args.json
        else to_markdown(target_role, result)
    )

    if args.output:
        if args.output.exists() and not args.force:
            print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)

    if not result["ready"]:
        print(
            f"GAPS FOUND: {len(result['below_threshold'])} below threshold, "
            f"{len(result['not_assessed'])} never assessed (threshold={args.threshold})",
            file=sys.stderr,
        )
        return 1

    print(f"NO GAPS: all {len(required_skills)} required skill(s) meet or exceed threshold {args.threshold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
