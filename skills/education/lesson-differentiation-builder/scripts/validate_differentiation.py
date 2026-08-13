#!/usr/bin/env python3
"""Validate a K-12 lesson-differentiation JSON record -- an existing lesson
adapted into below/at/above grade-level proficiency tiers, following the
Tomlinson differentiation framework -- then optionally render a teacher-facing
plan and/or the three student-facing tier worksheets to Markdown.

The core structural discipline this validator encodes: everything shared
across tiers (essential question, core task set, vocabulary, reflection
prompt, anchor activity) lives ONCE in the `shared` block. Each tier's
`worksheet_items` references those core tasks by key (`from_shared:<key>`)
instead of retyping them, and this script mechanically checks that every
tier's worksheet references the EXACT SAME set of core-task keys -- so tiers
cannot drift onto different content, only differ in how that content is
scaffolded (Below) or extended (Above). This is a deterministic structural
stand-in for what a shared-content render pipeline enforces by construction;
here it is enforced by cross-checking references instead.

This checks STRUCTURE and cross-references -- it does not judge whether the
scaffolds/extension are actually pedagogically well-designed, factually
correct, or age-appropriate; that stays a human/agent authoring judgment call.
Stdlib only, local, deterministic -- no AI/network call of any kind.

Errors block (exit 1); warnings are quality signals worth acting on but don't
block (exit 0 with warnings printed).

Usage:
    python validate_differentiation.py plan.json [--render-plan plan.md] [--render-worksheets DIR] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TOP_FIELDS = ("subject", "grade", "topic", "source_lesson_summary", "shared", "tiers")
REQUIRED_TIER_KEYS = ("below", "at", "above")
EXPECTED_GROUP_LABEL = {"below": "Group A", "at": "Group B", "above": "Group C"}
SCAFFOLD_DENSITY_CAP = 6


class DifferentiationError(Exception):
    pass


def _ref_key(ref: str) -> str | None:
    """Extract the shared-core-task key out of a 'from_shared:<key>' ref, or None if malformed."""
    if not isinstance(ref, str) or not ref.startswith("from_shared:"):
        return None
    key = ref[len("from_shared:"):]
    return key or None


def validate(plan: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_TOP_FIELDS:
        if field not in plan:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    for field in ("subject", "grade", "topic", "source_lesson_summary"):
        if not str(plan.get(field, "")).strip():
            errors.append(f"{field} must be a non-empty string")

    shared = plan["shared"]
    if not isinstance(shared, dict):
        errors.append("shared must be an object")
        return errors, warnings

    if not str(shared.get("essential_question", "")).strip():
        errors.append("shared.essential_question is required and must be non-empty")

    if not str(shared.get("reflect_prompt", "")).strip():
        errors.append("shared.reflect_prompt is required and must be non-empty -- every tier's worksheet must end with the same open-ended reflection")

    core_tasks = shared.get("core_tasks")
    core_task_keys: set[str] = set()
    if not isinstance(core_tasks, list) or len(core_tasks) == 0:
        errors.append("shared.core_tasks must be a non-empty list")
        core_tasks = []
    else:
        for i, ct in enumerate(core_tasks):
            if not isinstance(ct, dict):
                errors.append(f"shared.core_tasks[{i}] must be an object")
                continue
            key = ct.get("key")
            if not str(key or "").strip():
                errors.append(f"shared.core_tasks[{i}]: key is required and must be non-empty")
                continue
            if key in core_task_keys:
                errors.append(f"shared.core_tasks has a duplicate key: {key!r}")
            core_task_keys.add(key)
            if not str(ct.get("task", "")).strip():
                errors.append(f"shared.core_tasks[{i}] (key={key!r}): task is required and must be non-empty")

    for i, vocab in enumerate(shared.get("vocabulary", []) or []):
        if not isinstance(vocab, dict) or not str(vocab.get("term", "")).strip() or not str(vocab.get("meaning", "")).strip():
            warnings.append(f"shared.vocabulary[{i}] is missing term or meaning -- vocabulary entries should be complete or omitted")

    tiers = plan["tiers"]
    if not isinstance(tiers, dict):
        errors.append("tiers must be an object")
        return errors, warnings

    actual_tier_keys = set(tiers.keys())
    expected_tier_keys = set(REQUIRED_TIER_KEYS)
    missing_tiers = expected_tier_keys - actual_tier_keys
    extra_tiers = actual_tier_keys - expected_tier_keys
    if missing_tiers:
        errors.append(f"tiers is missing required tier(s): {sorted(missing_tiers)} (fixed set: below/at/above -- cannot reduce to fewer tiers)")
    if extra_tiers:
        errors.append(f"tiers has unrecognized tier key(s): {sorted(extra_tiers)} (fixed set: below/at/above -- not a 4th tier or a renamed one)")

    for tier_name in REQUIRED_TIER_KEYS:
        if tier_name not in tiers:
            continue
        tier = tiers[tier_name]
        if not isinstance(tier, dict):
            errors.append(f"tiers.{tier_name} must be an object")
            continue

        group_label = tier.get("group_label")
        expected_label = EXPECTED_GROUP_LABEL[tier_name]
        if group_label != expected_label:
            errors.append(f"tiers.{tier_name}.group_label must be {expected_label!r} (fixed convention: Below=Group A, At=Group B, Above=Group C), got {group_label!r}")

        if tier_name in ("below", "above"):
            if not str(tier.get("entry_point", "")).strip():
                errors.append(f"tiers.{tier_name}.entry_point is required and must be non-empty -- state where this tier's students start relative to the core task")

        if tier_name == "below":
            scaffolds = tier.get("scaffolds")
            if not isinstance(scaffolds, list) or len(scaffolds) == 0:
                errors.append("tiers.below.scaffolds must be a non-empty list -- the Below tier needs at least one explicit support")
                scaffolds = []
            else:
                empty_scaffolds = [i for i, s in enumerate(scaffolds) if not str(s).strip()]
                if empty_scaffolds:
                    errors.append(f"tiers.below.scaffolds has empty entries at index(es): {empty_scaffolds}")
                if len(scaffolds) > SCAFFOLD_DENSITY_CAP:
                    warnings.append(f"tiers.below.scaffolds has {len(scaffolds)} entries, more than the {SCAFFOLD_DENSITY_CAP} density-cap guideline -- too many simultaneous supports can be as inaccessible as too few")

        if tier_name == "above":
            extension = str(tier.get("extension", "")).strip()
            if not extension:
                errors.append("tiers.above.extension is required and must be non-empty -- Above must have a genuine qualitatively-different challenge, not just more of the core task")
            else:
                for ct in core_tasks:
                    if isinstance(ct, dict) and extension.lower() == str(ct.get("task", "")).strip().lower():
                        warnings.append(f"tiers.above.extension is verbatim-identical to shared.core_tasks (key={ct.get('key')!r}) -- verify this is a genuine extension, not just a repeat of the core task")
                        break

        items = tier.get("worksheet_items")
        if not isinstance(items, list) or len(items) == 0:
            errors.append(f"tiers.{tier_name}.worksheet_items must be a non-empty list")
            items = []

        tier_ref_keys: list[str] = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"tiers.{tier_name}.worksheet_items[{i}] must be an object")
                continue
            ref = item.get("ref")
            ref_key = _ref_key(ref)
            if ref_key is None:
                errors.append(f"tiers.{tier_name}.worksheet_items[{i}].ref must be of the form 'from_shared:<key>', got {ref!r}")
                continue
            if core_task_keys and ref_key not in core_task_keys:
                errors.append(f"tiers.{tier_name}.worksheet_items[{i}].ref points at unknown shared.core_tasks key {ref_key!r}")
                continue
            tier_ref_keys.append(ref_key)

            if tier_name == "at" and str(item.get("modification", "")).strip():
                warnings.append(f"tiers.at.worksheet_items[{i}] has a non-empty modification -- the At tier is the grade-level default and should normally use the core task as-is; if a real change is needed, verify it isn't actually a Below/Above tweak")

        if core_task_keys:
            tier_key_set = set(tier_ref_keys)
            missing_refs = core_task_keys - tier_key_set
            if missing_refs:
                errors.append(f"tiers.{tier_name}.worksheet_items is missing reference(s) to shared.core_tasks key(s) {sorted(missing_refs)} -- every tier must cover the same core task set (only presentation may differ)")
            dup_refs = [k for k in tier_ref_keys if tier_ref_keys.count(k) > 1]
            if dup_refs:
                errors.append(f"tiers.{tier_name}.worksheet_items references the same shared.core_tasks key more than once: {sorted(set(dup_refs))}")

    return errors, warnings


def _core_task_lookup(shared: dict) -> dict[str, str]:
    return {
        ct["key"]: ct.get("task", "")
        for ct in shared.get("core_tasks", [])
        if isinstance(ct, dict) and str(ct.get("key", "")).strip()
    }


def to_markdown_plan(plan: dict) -> str:
    """Teacher-facing differentiation plan: overview + all three tiers side by side, including teacher-only rationale (entry_point, scaffold list, extension)."""
    shared = plan["shared"]
    tasks = _core_task_lookup(shared)
    lines = [
        f"# Differentiation Plan: {plan['topic']}",
        "",
        f"**Subject**: {plan['subject']} | **Grade**: {plan['grade']}" + (f" | **Standard**: {plan['standard']}" if str(plan.get("standard", "")).strip() else ""),
        "",
        f"**Source lesson**: {plan['source_lesson_summary']}",
        "",
    ]
    if str(plan.get("learner_needs", "")).strip():
        lines.extend([f"**Learner needs on file**: {plan['learner_needs']}", ""])

    lines.extend([
        "## Essential question (shared by all tiers)",
        "",
        shared.get("essential_question", ""),
        "",
        "## Core tasks (shared by all tiers)",
        "",
    ])
    for key, task in tasks.items():
        lines.append(f"- **{key}**: {task}")
    lines.append("")

    if shared.get("vocabulary"):
        lines.extend(["## Shared vocabulary", ""])
        for v in shared["vocabulary"]:
            if isinstance(v, dict):
                lines.append(f"- **{v.get('term', '')}**: {v.get('meaning', '')}")
        lines.append("")

    tier_titles = {"below": "Below grade-level (Group A)", "at": "At grade-level (Group B)", "above": "Above grade-level (Group C)"}
    for tier_name in REQUIRED_TIER_KEYS:
        tier = plan["tiers"][tier_name]
        lines.extend(["", f"## {tier_titles[tier_name]}", ""])
        if "entry_point" in tier:
            lines.append(f"**Entry point**: {tier['entry_point']}")
        if tier_name == "below":
            lines.append("")
            lines.append("**Scaffolds**:")
            for s in tier.get("scaffolds", []):
                lines.append(f"- {s}")
        if tier_name == "above":
            lines.append("")
            lines.append(f"**Extension**: {tier.get('extension', '')}")
        lines.append("")
        lines.append("**Worksheet tasks**:")
        for item in tier.get("worksheet_items", []):
            key = _ref_key(item.get("ref", ""))
            base_task = tasks.get(key, "")
            mod = str(item.get("modification", "")).strip()
            line = f"- {key}: {base_task}"
            if mod:
                line += f" -- *modification*: {mod}"
            lines.append(line)

    lines.extend(["", "## Shared close (every tier)", ""])
    if str(shared.get("anchor_activity", "")).strip():
        lines.append(f"**Anchor activity (early finishers)**: {shared['anchor_activity']}")
    lines.append(f"**Reflection prompt**: {shared.get('reflect_prompt', '')}")

    return "\n".join(lines) + "\n"


def to_markdown_worksheet(plan: dict, tier_name: str) -> str:
    """Student-facing worksheet for one tier: tasks (with any modification/extension), anchor activity, reflect prompt. No teacher-only rationale (entry_point)."""
    shared = plan["shared"]
    tasks = _core_task_lookup(shared)
    tier = plan["tiers"][tier_name]

    lines = [
        f"# {tier.get('group_label', '')} Worksheet: {plan['topic']}",
        "",
        f"**Subject**: {plan['subject']} | **Grade**: {plan['grade']}",
        "",
    ]

    if tier_name == "below" and tier.get("scaffolds"):
        lines.extend(["## Supports", ""])
        for s in tier["scaffolds"]:
            lines.append(f"- {s}")
        lines.append("")

    lines.extend(["## Tasks", ""])
    for item in tier.get("worksheet_items", []):
        key = _ref_key(item.get("ref", ""))
        base_task = tasks.get(key, "")
        mod = str(item.get("modification", "")).strip()
        lines.append(f"- {base_task}" + (f" ({mod})" if mod else ""))
    lines.append("")

    if tier_name == "above" and str(tier.get("extension", "")).strip():
        lines.extend(["## Extension", "", tier["extension"], ""])

    if str(shared.get("anchor_activity", "")).strip():
        lines.extend(["## If you finish early", "", shared["anchor_activity"], ""])

    lines.extend(["## Reflect", "", shared.get("reflect_prompt", "")])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path, help="Path to a differentiation-plan JSON file (see assets/differentiation_template.json)")
    parser.add_argument("--render-plan", type=Path, default=None, help="If validation passes with no errors, render the teacher-facing plan to this Markdown path")
    parser.add_argument("--render-worksheets", type=Path, default=None, help="If validation passes with no errors, render worksheet_below.md/worksheet_at.md/worksheet_above.md into this directory")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(plan, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(plan)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: structurally complete differentiation plan (below/at/above tiers cover the same core task set). This confirms structure only, not pedagogical quality.")

    if args.render_plan:
        if args.render_plan.exists() and not args.force:
            print(f"REFUSED: {args.render_plan} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render_plan.write_text(to_markdown_plan(plan), encoding="utf-8")
        print(f"OK: rendered teacher plan to {args.render_plan}")

    if args.render_worksheets:
        out_dir = args.render_worksheets
        out_dir.mkdir(parents=True, exist_ok=True)
        for tier_name in REQUIRED_TIER_KEYS:
            target = out_dir / f"worksheet_{tier_name}.md"
            if target.exists() and not args.force:
                print(f"REFUSED: {target} already exists, use --force to overwrite", file=sys.stderr)
                return 2
            target.write_text(to_markdown_worksheet(plan, tier_name), encoding="utf-8")
            print(f"OK: rendered {tier_name} worksheet to {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
