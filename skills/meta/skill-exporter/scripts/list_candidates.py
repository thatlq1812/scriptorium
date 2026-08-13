#!/usr/bin/env python3
"""List registry skills matching a set of tag filters, as candidates for
export_bundle.py. Stdlib only (json, argparse), local, deterministic --
reads registry/skills.json, no network.

HARD EXCLUSION (never overridable by a filter, and enforced again by
export_bundle.py -- this is not just a display filter): a skill with
license_debt != null, security_audit.status != "passed", OR
operational_status.state == "paused" is never listed as a candidate.
registry/SCHEMA.md already states a license-debt skill "may not be
distributed/published outside the internal repo while in debt" -- this is
the first place in the project that rule has real teeth, since nothing
exported anything before this skill existed. operational_status (added
2026-07-29) covers a skill that passed audit but was deliberately paused by
the owner for a reason distinct from license/security -- see
registry/SCHEMA.md's operational_status field.

Filters are OR-within-axis, AND-across-axis: --domain legal general matches
a skill tagged either legal OR general, but if --task-type is also given,
the skill must additionally match that.

Exit codes: 0 = ran (0 or more candidates), 2 = malformed registry.

Usage:
    python list_candidates.py [--domain D [D ...]] [--task-type T [T ...]] [--object-type O [O ...]] [-o candidates.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REGISTRY_PATH = Path(__file__).resolve().parents[3].parent / "registry" / "skills.json"


def load_registry() -> list[dict]:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED registry: {exc}", file=sys.stderr)
        raise SystemExit(2)
    skills = data.get("skills") if isinstance(data, dict) else data
    if not isinstance(skills, list):
        print("MALFORMED registry: expected a list of skills (top-level or under 'skills')", file=sys.stderr)
        raise SystemExit(2)
    return skills


def is_exportable(skill: dict) -> tuple[bool, str]:
    if skill.get("license_debt") is not None:
        return False, "license_debt is set -- may not be distributed outside the internal repo (registry/SCHEMA.md)"
    audit = skill.get("security_audit", {})
    if audit.get("status") != "passed":
        return False, f"security_audit.status is {audit.get('status')!r}, not 'passed'"
    op_status = skill.get("operational_status")
    if isinstance(op_status, dict) and op_status.get("state") == "paused":
        return False, f"operational_status is paused -- {op_status.get('reason', 'no reason recorded')}"
    if isinstance(op_status, dict) and op_status.get("state") == "superseded":
        return False, f"operational_status is superseded by '{op_status.get('superseded_by', '?')}' -- {op_status.get('reason', 'no reason recorded')}"
    return True, ""


def matches(skill: dict, domain: list[str], task_type: list[str], object_type: list[str]) -> bool:
    tags = skill.get("tags", {})
    if domain and not (set(tags.get("domain", [])) & set(domain)):
        return False
    if task_type and not (set(tags.get("task_type", [])) & set(task_type)):
        return False
    if object_type and not (set(tags.get("object_type", [])) & set(object_type)):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domain", nargs="*", default=[])
    parser.add_argument("--task-type", nargs="*", default=[])
    parser.add_argument("--object-type", nargs="*", default=[])
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    skills = load_registry()
    excluded = []
    candidates = []
    for s in skills:
        ok, reason = is_exportable(s)
        if not ok:
            excluded.append((s["skill_id"], reason))
            continue
        if matches(s, args.domain, args.task_type, args.object_type):
            candidates.append(s)

    rows = [
        {
            "skill_id": s["skill_id"],
            "version": s["version"],
            "domain": s.get("tags", {}).get("domain", []),
            "task_type": s.get("tags", {}).get("task_type", []),
            "risk_tier": s.get("tags", {}).get("risk_tier"),
            "quality_score": s.get("quality_score"),
        }
        for s in candidates
    ]

    out = json.dumps({"candidates": rows}, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
    print(f"{len(rows)} candidate(s) match:")
    for r in rows:
        print(f"  - {r['skill_id']} v{r['version']} (domain={r['domain']}, task_type={r['task_type']}, risk_tier={r['risk_tier']})")
    if not args.output and rows:
        print("", file=sys.stderr)
        print("(pass -o to also write JSON for export_bundle.py)", file=sys.stderr)

    if excluded:
        print(f"\n{len(excluded)} skill(s) excluded from candidacy (license_debt, failed security_audit, or paused):", file=sys.stderr)
        for skill_id, reason in excluded:
            print(f"  - {skill_id}: {reason}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
