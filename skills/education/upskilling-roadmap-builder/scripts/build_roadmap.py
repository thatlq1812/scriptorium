#!/usr/bin/env python3
"""Compute a caller-declared skill gap (target-role skills minus current
skills) and sequence it into a day-by-day study/review roadmap.

This does NOT reinvent interleaved/spaced-repetition scheduling. It reuses
the exact round-robin-new-topics + periodic-review-everyone-so-far
algorithm from skills/education/study-plan-builder/scripts/build_study_plan.py by
importing its functions directly (see "_import_scheduling_core" below) --
that skill's own scheduling core is the source of truth, this script only
adds gap computation on top of it. skills/education/study-plan-builder/ itself is
never modified.

Stdlib only (json, argparse, math via the imported module), local,
deterministic, no AI/network of any kind. Never invents a current-skill or
target-skill list -- both come from the caller-supplied input file.

Algorithm:
    1. Parse `current_skills` (list of skill names the learner already has)
       and `target_skills` (list of {name, weight} the target role needs).
    2. Gap = target_skills entries whose name does not case-insensitively
       match any current_skills entry (after trimming whitespace).
    3. The gap list becomes the "topics" fed into study-plan-builder's own
       interleave_new_sessions()/build_schedule() -- same weight semantics
       (1-5, default 2), same round-robin interleaving, same periodic
       review cycling, same capacity-refusal behavior.
    4. If the gap is empty, this refuses to produce a schedule (nothing to
       schedule) and reports so explicitly rather than emitting an empty
       plan.

Usage:
    python build_roadmap.py skills_gap.json --days 21 --output roadmap.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class RoadmapError(Exception):
    """Malformed input -- exit 2."""


class RoadmapValidationFailure(Exception):
    """Well-formed input that fails a business-rule check (e.g. not enough
    schedule capacity for the computed gap) -- exit 1."""


def _import_scheduling_core():
    """Import study-plan-builder's scheduling functions directly rather
    than duplicating the algorithm. study-plan-builder is a sibling skill
    under skills/, resolved relative to this script's own location so it
    works regardless of the caller's cwd."""
    study_plan_builder = next(Path(__file__).resolve().parents[3].glob("*/study-plan-builder"), None)
    if study_plan_builder is None:
        raise RoadmapError(
            "cannot import scheduling core: 'study-plan-builder' not found as a sibling "
            "skill folder under skills/<domain>/study-plan-builder"
        )
    spb_scripts = study_plan_builder / "scripts"
    if str(spb_scripts) not in sys.path:
        sys.path.insert(0, str(spb_scripts))
    try:
        import build_study_plan as spb  # type: ignore
    except ImportError as exc:
        raise RoadmapError(
            f"cannot import scheduling core from study-plan-builder at {spb_scripts} "
            f"(expected build_study_plan.py to exist there): {exc}"
        ) from exc
    return spb


def load_gap_input(path: Path) -> tuple[str, list[str], list[dict]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoadmapError(f"cannot read skills-gap file: {exc}") from exc

    if not isinstance(data, dict):
        raise RoadmapError("skills-gap file must contain a JSON object")

    target_role = data.get("target_role")
    if not isinstance(target_role, str) or not target_role.strip():
        raise RoadmapError("'target_role' must be a non-empty string")

    current_skills = data.get("current_skills", [])
    if not isinstance(current_skills, list):
        raise RoadmapError("'current_skills' must be a list")
    normalized_current: list[str] = []
    for i, s in enumerate(current_skills):
        if not isinstance(s, str) or not s.strip():
            raise RoadmapError(f"current_skills[{i}] must be a non-empty string")
        normalized_current.append(s.strip())

    target_skills = data.get("target_skills")
    if not isinstance(target_skills, list) or not target_skills:
        raise RoadmapError("'target_skills' must be a non-empty list")

    normalized_target: list[dict] = []
    seen_names: set[str] = set()
    for i, t in enumerate(target_skills):
        if not isinstance(t, dict) or not t.get("name"):
            raise RoadmapError(f"target_skills[{i}] must be an object with a non-empty 'name'")
        name = str(t["name"]).strip()
        key = name.lower()
        if key in seen_names:
            raise RoadmapError(f"duplicate target_skills entry: {name!r}")
        seen_names.add(key)
        weight = t.get("weight", 2)
        if not isinstance(weight, int) or isinstance(weight, bool) or not (1 <= weight <= 5):
            raise RoadmapError(f"target_skills[{i}] ({name!r}) weight must be an integer 1-5, got {weight!r}")
        normalized_target.append({"name": name, "weight": weight})

    return target_role.strip(), normalized_current, normalized_target


def compute_gap(current_skills: list[str], target_skills: list[dict]) -> tuple[list[dict], list[str]]:
    """Returns (gap_topics, already_held) -- gap_topics keeps the same
    {name, weight} shape study-plan-builder's scheduling core expects."""
    held = {s.lower() for s in current_skills}
    gap: list[dict] = []
    already_held: list[str] = []
    for t in target_skills:
        if t["name"].lower() in held:
            already_held.append(t["name"])
        else:
            gap.append(t)
    return gap, already_held


def to_markdown(target_role: str, current_skills: list[str], already_held: list[str],
                 gap: list[dict], schedule: list[dict]) -> str:
    lines = [
        f"# Upskilling roadmap -- {target_role}",
        "",
        f"Current skills declared: {', '.join(current_skills) if current_skills else '(none declared)'}",
        f"Target-role skills already held (excluded from gap): {', '.join(already_held) if already_held else '(none)'}",
        f"Skill gap to schedule: {', '.join(t['name'] for t in gap)}",
        "",
        "| Day | Session | Type | Skill |",
        "| --- | --- | --- | --- |",
    ]
    for e in schedule:
        lines.append(f"| {e['day']} | {e['session']} | {e['type']} | {e['topic']} |")
    lines.append("")
    lines.append("## Checklist")
    lines.append("")
    current_day = None
    for e in schedule:
        if e["day"] != current_day:
            current_day = e["day"]
            lines.append(f"### Day {current_day}")
        lines.append(f"- [ ] ({e['type']}) {e['topic']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skills_gap", type=Path, help="Path to a skills-gap JSON file (see assets/skills_gap_template.json)")
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--sessions-per-day", type=int, default=1)
    parser.add_argument("--review-every", type=int, default=4, help="Every Nth session is a review session (default 4)")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print raw JSON (gap + schedule) instead of Markdown")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    # Guard-clause validation of our own CLI config, kept separate from the
    # imported scheduling core's capacity check so config mistakes (exit 2)
    # and genuine capacity shortfalls (exit 1) get distinct exit codes.
    if args.days < 1:
        print("REFUSED: --days must be >= 1", file=sys.stderr)
        return 2
    if args.sessions_per_day < 1:
        print("REFUSED: --sessions-per-day must be >= 1", file=sys.stderr)
        return 2
    if args.review_every < 2:
        print("REFUSED: --review-every must be >= 2 (a value of 1 would leave zero new-study slots)", file=sys.stderr)
        return 2

    try:
        spb = _import_scheduling_core()
        target_role, current_skills, target_skills = load_gap_input(args.skills_gap)
    except RoadmapError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    gap, already_held = compute_gap(current_skills, target_skills)

    if not gap:
        print(
            f"OK: no skill gap for target role {target_role!r} -- every target-role skill "
            f"({', '.join(already_held) if already_held else '(none declared)'}) is already in current_skills. "
            f"Nothing to schedule."
        )
        return 0

    try:
        schedule = spb.build_schedule(gap, args.days, args.sessions_per_day, args.review_every)
    except spb.PlanError as exc:
        print(f"REFUSED (validation failure): {exc}", file=sys.stderr)
        return 1

    if args.json:
        output_text = json.dumps(
            {
                "target_role": target_role,
                "current_skills": current_skills,
                "already_held": already_held,
                "gap": gap,
                "schedule": schedule,
            },
            indent=2,
            ensure_ascii=False,
        )
    else:
        output_text = to_markdown(target_role, current_skills, already_held, gap, schedule)

    if args.output:
        if args.output.exists() and not args.force:
            print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote a {len(schedule)}-session roadmap ({len(gap)} gap skill(s)) to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
