#!/usr/bin/env python3
"""Deterministic exam-readiness checklist validator.

Checks a caller-declared study log's covered topics against a
caller-declared certification exam blueprint's domain/objective list, and
flags any objective not covered. This NEVER asserts real exam content
itself -- the blueprint (certification name, domains, weightings,
objective text) and the study log (topics covered) are always
caller-supplied input, never invented or fabricated by this script. When a
concrete blueprint example is bundled as a fixture (see
assets/exam_blueprint_template.json), it must cite the real certification
body's own published exam guide via 'source_citation'.

Matching is exact, case-insensitive, whitespace-trimmed string equality
between an objective's text and a study-log entry -- no fuzzy/semantic
matching, same "never guess a match" discipline as legal-form-filler and
personal-profile-manager's autofill.py. A learner who logged a topic in
different words than the blueprint's objective text will show as
uncovered; that is a caller-input precision problem, not something this
script silently resolves by guessing.

Stdlib only (json, argparse), local, deterministic, no AI/network calls.

Usage:
    python check_exam_readiness.py blueprint.json study_log.json \
        [--threshold-percent 100] [--output report.md] [--json]

Exit 0 = every domain meets the coverage threshold (exam-ready).
Exit 1 = well-formed input but at least one domain (or the overall total)
         is below --threshold-percent -- gaps are flagged, not a crash.
Exit 2 = malformed input (missing/invalid fields, bad JSON, structural
         violations such as duplicate objective text or an out-of-range
         weight).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class PrepError(Exception):
    """Malformed input -- exit 2."""


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def load_blueprint(path: Path) -> tuple[str, str, list[dict]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrepError(f"cannot read blueprint file: {exc}") from exc

    if not isinstance(data, dict):
        raise PrepError("blueprint file must contain a JSON object")

    cert_name = data.get("certification_name")
    if not isinstance(cert_name, str) or not cert_name.strip():
        raise PrepError("'certification_name' must be a non-empty string")

    citation = data.get("source_citation")
    if not isinstance(citation, str) or not citation.strip():
        raise PrepError(
            "'source_citation' must be a non-empty string naming the real certification body's "
            "published exam blueprint this data came from"
        )

    domains = data.get("domains")
    if not isinstance(domains, list) or not domains:
        raise PrepError("'domains' must be a non-empty list")

    seen_objective_norms: set[str] = set()
    seen_domain_names: set[str] = set()
    normalized_domains: list[dict] = []
    for i, d in enumerate(domains):
        if not isinstance(d, dict):
            raise PrepError(f"domains[{i}] must be an object")
        domain_name = d.get("domain_name")
        if not isinstance(domain_name, str) or not domain_name.strip():
            raise PrepError(f"domains[{i}] must have a non-empty 'domain_name'")
        domain_key = _norm(domain_name)
        if domain_key in seen_domain_names:
            raise PrepError(f"duplicate domain_name: {domain_name!r}")
        seen_domain_names.add(domain_key)

        weight = d.get("weight_percent")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or not (0 <= weight <= 100):
            raise PrepError(f"domains[{i}] ({domain_name!r}) weight_percent must be a number 0-100, got {weight!r}")

        objectives = d.get("objectives")
        if not isinstance(objectives, list) or not objectives:
            raise PrepError(f"domains[{i}] ({domain_name!r}) 'objectives' must be a non-empty list")

        normalized_objectives: list[str] = []
        for j, o in enumerate(objectives):
            if not isinstance(o, str) or not o.strip():
                raise PrepError(f"domains[{i}].objectives[{j}] must be a non-empty string")
            obj_norm = _norm(o)
            if obj_norm in seen_objective_norms:
                raise PrepError(f"duplicate objective text across the blueprint: {o!r}")
            seen_objective_norms.add(obj_norm)
            normalized_objectives.append(o.strip())

        normalized_domains.append({
            "domain_name": domain_name.strip(),
            "weight_percent": weight,
            "objectives": normalized_objectives,
        })

    return cert_name.strip(), citation.strip(), normalized_domains


def load_study_log(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrepError(f"cannot read study log file: {exc}") from exc

    if not isinstance(data, dict):
        raise PrepError("study log file must contain a JSON object")

    topics = data.get("topics_covered")
    if not isinstance(topics, list) or not topics:
        raise PrepError("'topics_covered' must be a non-empty list")

    seen: set[str] = set()
    normalized: list[str] = []
    for i, t in enumerate(topics):
        if not isinstance(t, str) or not t.strip():
            raise PrepError(f"topics_covered[{i}] must be a non-empty string")
        key = _norm(t)
        if key in seen:
            raise PrepError(f"duplicate topics_covered entry: {t!r}")
        seen.add(key)
        normalized.append(t.strip())

    return normalized


def evaluate(domains: list[dict], topics_covered: list[str], threshold_percent: float) -> dict:
    covered_norms = {_norm(t) for t in topics_covered}

    domain_reports = []
    total_objectives = 0
    total_covered = 0

    for d in domains:
        objectives = d["objectives"]
        covered = [o for o in objectives if _norm(o) in covered_norms]
        uncovered = [o for o in objectives if _norm(o) not in covered_norms]
        coverage_percent = round(100.0 * len(covered) / len(objectives), 2)
        total_objectives += len(objectives)
        total_covered += len(covered)
        domain_reports.append({
            "domain_name": d["domain_name"],
            "weight_percent": d["weight_percent"],
            "total_objectives": len(objectives),
            "covered_count": len(covered),
            "coverage_percent": coverage_percent,
            "uncovered_objectives": uncovered,
            "ready": coverage_percent >= threshold_percent,
        })

    overall_coverage_percent = round(100.0 * total_covered / total_objectives, 2) if total_objectives else 0.0

    matched_topic_norms = set()
    for d in domains:
        for o in d["objectives"]:
            if _norm(o) in covered_norms:
                matched_topic_norms.add(_norm(o))
    unmatched_topics = [t for t in topics_covered if _norm(t) not in matched_topic_norms]

    ready = overall_coverage_percent >= threshold_percent and all(dr["ready"] for dr in domain_reports)

    return {
        "overall_coverage_percent": overall_coverage_percent,
        "ready": ready,
        "domains": domain_reports,
        "unmatched_study_log_topics": unmatched_topics,
    }


def to_markdown(cert_name: str, citation: str, threshold_percent: float, result: dict) -> str:
    lines = [
        f"# Exam readiness report -- {cert_name}",
        "",
        f"Blueprint source: {citation}",
        f"Coverage threshold required per domain: {threshold_percent}%",
        f"Overall coverage: {result['overall_coverage_percent']}%",
        f"Overall status: {'READY' if result['ready'] else 'NOT READY'}",
        "",
        "| Domain | Weight % | Covered | Total | Coverage % | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for d in result["domains"]:
        status = "ready" if d["ready"] else "GAP"
        lines.append(
            f"| {d['domain_name']} | {d['weight_percent']} | {d['covered_count']} | "
            f"{d['total_objectives']} | {d['coverage_percent']} | {status} |"
        )
    lines.append("")
    for d in result["domains"]:
        if d["uncovered_objectives"]:
            lines.append(f"## Uncovered objectives -- {d['domain_name']}")
            for o in d["uncovered_objectives"]:
                lines.append(f"- [ ] {o}")
            lines.append("")
    if result["unmatched_study_log_topics"]:
        lines.append("## Study-log topics that did not match any blueprint objective")
        lines.append("(exact-match only -- check wording against the blueprint if this looks wrong)")
        for t in result["unmatched_study_log_topics"]:
            lines.append(f"- {t}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("blueprint", type=Path, help="Path to an exam blueprint JSON file (see assets/exam_blueprint_template.json)")
    parser.add_argument("study_log", type=Path, help="Path to a study log JSON file (see assets/study_log_template.json)")
    parser.add_argument("--threshold-percent", type=float, default=100.0, help="Minimum per-domain coverage percent required to be 'ready' (default 100)")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print raw JSON report instead of Markdown")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not (0 <= args.threshold_percent <= 100):
        print("REFUSED: --threshold-percent must be between 0 and 100", file=sys.stderr)
        return 2

    try:
        cert_name, citation, domains = load_blueprint(args.blueprint)
        topics_covered = load_study_log(args.study_log)
    except PrepError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    result = evaluate(domains, topics_covered, args.threshold_percent)

    output_text = (
        json.dumps({"certification_name": cert_name, "source_citation": citation, **result}, indent=2, ensure_ascii=False)
        if args.json
        else to_markdown(cert_name, citation, args.threshold_percent, result)
    )

    if args.output:
        if args.output.exists() and not args.force:
            print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)

    if not result["ready"]:
        gaps = sum(1 for d in result["domains"] if not d["ready"])
        print(f"NOT READY: {gaps} domain(s) below {args.threshold_percent}% threshold (overall {result['overall_coverage_percent']}%)", file=sys.stderr)
        return 1

    print(f"READY: overall coverage {result['overall_coverage_percent']}%, all domains at/above {args.threshold_percent}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
