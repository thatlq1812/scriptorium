#!/usr/bin/env python3
"""Fill a caller-supplied form template's fields from caller-supplied data,
validating that every required field has a value and flagging any data key
that doesn't match a declared field (likely a typo). Stdlib only (json,
argparse), local, deterministic -- no AI/network call of any kind.

The form template is ALWAYS caller-supplied, never hard-coded: this
project has no real government/company form data to bake in, so this is a
generic placeholder-filling engine, not a specific form's rules. Final
.docx rendering is out of scope here -- delegate to office-doc-creator
once a fill passes validation.

Exit codes: 0 = all required fields filled, 1 = missing required field(s),
2 = malformed input.

Usage:
    python fill_form.py form_template.json form_data.json [--render filled.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class FormError(Exception):
    pass


def load_template(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FormError(f"cannot read form template: {exc}") from exc
    fields = data.get("fields") if isinstance(data, dict) else None
    if not isinstance(fields, list) or not fields:
        raise FormError("form template must have a non-empty 'fields' list")
    names = set()
    for i, f in enumerate(fields):
        if not isinstance(f, dict) or not f.get("name") or not f.get("label"):
            raise FormError(f"fields[{i}] must be an object with non-empty 'name' and 'label'")
        if f["name"] in names:
            raise FormError(f"duplicate field name: {f['name']!r}")
        names.add(f["name"])
    return fields


def fill(fields: list[dict], data: dict) -> tuple[dict, list[str], list[str]]:
    filled: dict = {}
    missing_required: list[str] = []
    declared_names = {f["name"] for f in fields}

    for f in fields:
        value = data.get(f["name"])
        if value is None or (isinstance(value, str) and not value.strip()):
            if f.get("required", True):
                missing_required.append(f["name"])
            filled[f["name"]] = None
        else:
            filled[f["name"]] = value

    unknown_keys = [k for k in data if k not in declared_names]
    return filled, missing_required, unknown_keys


def to_markdown(form_name: str, fields: list[dict], filled: dict) -> str:
    lines = [f"# {form_name}", ""]
    for f in fields:
        value = filled.get(f["name"])
        lines.append(f"**{f['label']}**: {value if value is not None else '(chưa điền)'}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("template", type=Path, help="Path to a form template JSON file (see assets/form_template.json)")
    parser.add_argument("data", type=Path, help="Path to a form data JSON file (see assets/form_data_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        template = json.loads(args.template.read_text(encoding="utf-8"))
        fields = load_template(args.template)
    except FormError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: cannot read form data: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("MALFORMED: form data must be a JSON object", file=sys.stderr)
        return 2

    filled, missing_required, unknown_keys = fill(fields, data)

    if unknown_keys:
        print(f"NOTE: {len(unknown_keys)} data key(s) don't match any declared field (likely a typo, ignored): {unknown_keys}")

    if missing_required:
        print(f"INCOMPLETE: {len(missing_required)} required field(s) not filled: {missing_required}")
        return 1

    print(f"OK: all required fields filled ({len(fields)} total field(s)).")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(template.get("form_name", "Form"), fields, filled), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
