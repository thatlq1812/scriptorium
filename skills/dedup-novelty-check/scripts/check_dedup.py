#!/usr/bin/env python3
"""Check a candidate skill against registry/skills.json for overlap before
skill-creator starts. Stdlib only — no dependency, no venv needed.

Usage:
    python check_dedup.py --domain general legal --task-type document-conversion \
        --description "Chuyen doi tai lieu PDF thanh markdown co cau truc" \
        [--registry ../../../registry/skills.json] [--threshold 0.8]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_REGISTRY = Path(__file__).resolve().parents[2].parent / "registry" / "skills.json"


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ỹ0-9]+", text.lower()))


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def score_candidate(
    cand_domain: set[str],
    cand_task_type: set[str],
    cand_desc_tokens: set[str],
    existing: dict,
) -> dict:
    tags = existing.get("tags", {})
    domain_score = jaccard(cand_domain, set(tags.get("domain", [])))
    task_score = jaccard(cand_task_type, set(tags.get("task_type", [])))
    desc_tokens = tokenize(existing.get("elicited_from", ""))
    desc_score = jaccard(cand_desc_tokens, desc_tokens)
    combined = 0.4 * domain_score + 0.4 * task_score + 0.2 * desc_score
    return {
        "skill_id": existing["skill_id"],
        "domain_overlap": round(domain_score, 2),
        "task_type_overlap": round(task_score, 2),
        "description_overlap": round(desc_score, 2),
        "combined_score": round(combined, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", nargs="+", required=True)
    parser.add_argument("--task-type", nargs="+", required=True, dest="task_type")
    parser.add_argument("--description", required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    cand_domain = set(args.domain)
    cand_task_type = set(args.task_type)
    cand_desc_tokens = tokenize(args.description)

    results = [
        score_candidate(cand_domain, cand_task_type, cand_desc_tokens, s)
        for s in registry.get("skills", [])
    ]
    results.sort(key=lambda r: r["combined_score"], reverse=True)

    print(f"{'skill_id':<28}{'domain':<10}{'task_type':<12}{'desc':<8}{'combined':<10}")
    for r in results:
        print(
            f"{r['skill_id']:<28}{r['domain_overlap']:<10}{r['task_type_overlap']:<12}"
            f"{r['description_overlap']:<8}{r['combined_score']:<10}"
        )

    flagged = [r for r in results if r["combined_score"] >= args.threshold]
    if flagged:
        print(f"\nFLAGGED (>= {args.threshold}): {[r['skill_id'] for r in flagged]}")
        print("Ưu tiên mở rộng/versioning skill đã có thay vì tạo mới.")
        return 1

    print(f"\nKhông có skill nào vượt ngưỡng {args.threshold} — an toàn để tiếp tục skill-creator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
