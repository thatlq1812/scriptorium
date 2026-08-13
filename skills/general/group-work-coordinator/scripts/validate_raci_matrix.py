#!/usr/bin/env python3
"""Validate a group-project RACI matrix (Responsible / Accountable /
Consulted / Informed) against the standard RACI invariants: every task has
exactly one Accountable person, every person named anywhere in the matrix is
a declared group member, and no task is orphaned (assigned to nobody).
Stdlib only, local, deterministic -- no AI/network call of any kind.

This checks STRUCTURE only -- it never judges whether a given assignment is
a sensible division of labor, whether workload is balanced, or whether the
right person is Accountable for the right task; that stays the group's own
call. Errors block (exit 1); warnings are quality signals worth acting on
but don't block (exit 0 with warnings printed).

Usage:
    python validate_raci_matrix.py matrix.json [--render matrix.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_RACI_LETTERS = {"R", "A", "C", "I"}


def validate(matrix: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("project_name", "members", "tasks"):
        if field not in matrix:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    members = matrix["members"]
    if not isinstance(members, list) or not members or not all(isinstance(m, str) and m.strip() for m in members):
        errors.append("members must be a non-empty list of non-empty strings")
        return errors, warnings
    if len(set(members)) != len(members):
        errors.append(f"members must be distinct (no duplicate member name), got {members}")
    member_set = set(members)

    tasks = matrix["tasks"]
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty list")
        return errors, warnings

    seen_task_names: dict[str, int] = {}
    involved_members: set[str] = set()

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{i}] must be an object")
            continue

        task_name = task.get("task_name", "")
        if not isinstance(task_name, str) or not task_name.strip():
            errors.append(f"tasks[{i}]: task_name is required and must be non-empty")
            task_name = f"<tasks[{i}]>"
        else:
            if task_name in seen_task_names:
                errors.append(f"tasks[{i}] ({task_name!r}): duplicate task_name, already used by tasks[{seen_task_names[task_name]}]")
            seen_task_names[task_name] = i

        raci = task.get("raci")
        if not isinstance(raci, dict):
            errors.append(f"tasks[{i}] ({task_name}): raci must be an object mapping member name -> R/A/C/I")
            continue

        if not raci:
            errors.append(f"tasks[{i}] ({task_name}): orphan task -- raci is empty, nobody is assigned to it")
            continue

        accountable_count = 0
        responsible_count = 0

        for person, letter in raci.items():
            if person not in member_set:
                errors.append(f"tasks[{i}] ({task_name}): raci names {person!r}, who is not a declared group member ({sorted(member_set)})")
                continue

            involved_members.add(person)

            if not isinstance(letter, str) or letter not in VALID_RACI_LETTERS:
                errors.append(f"tasks[{i}] ({task_name}): raci[{person!r}] = {letter!r} is not a valid RACI letter (must be one of R, A, C, I)")
                continue

            if letter == "A":
                accountable_count += 1
            if letter == "R":
                responsible_count += 1

        if accountable_count == 0:
            errors.append(f"tasks[{i}] ({task_name}): no Accountable (A) person assigned -- every task needs exactly one")
        elif accountable_count > 1:
            errors.append(f"tasks[{i}] ({task_name}): {accountable_count} people assigned Accountable (A) -- every task needs exactly one, not multiple")

        if responsible_count == 0:
            warnings.append(f"tasks[{i}] ({task_name}): no Responsible (R) person assigned -- consider whether the Accountable person is also expected to do the work")

    uninvolved = member_set - involved_members
    if uninvolved:
        warnings.append(f"declared member(s) never appear in any task's raci: {sorted(uninvolved)} -- verify this is intentional")

    return errors, warnings


def to_markdown(matrix: dict) -> str:
    members = matrix["members"]
    tasks = matrix["tasks"]
    project_name = matrix["project_name"]

    lines = [f"# RACI Matrix: {project_name}", ""]
    header = ["Task"] + list(members)
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    for task in tasks:
        task_name = task.get("task_name", "")
        raci = task.get("raci", {})
        row = [task_name] + [raci.get(m, "") for m in members]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("R = Responsible, A = Accountable, C = Consulted, I = Informed.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("matrix", type=Path, help="Path to a RACI matrix JSON file (see assets/raci_matrix_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render a Markdown RACI table to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(matrix, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(matrix)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: every task has exactly one Accountable person, every named person is a declared group member, "
          "no orphan tasks. This confirms RACI structure only, not whether the assignment is a sensible division of labor.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(matrix), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
