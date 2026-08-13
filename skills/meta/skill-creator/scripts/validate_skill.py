#!/usr/bin/env python3
"""Mechanical validator for a Scriptorium SKILL.md against the agentskills.io
6-field spec plus Scriptorium's own required metadata fields.

This closes a gap found by comparing against github.com/anthropics/skills'
skill-creator/scripts/quick_validate.py: skill-creator's own SKILL.md
documents the structural constraints in prose (6-field spec, name==folder,
elicited_from never empty, 500-line cap) but had no script actually gating
them -- a weaker agent authoring a new skill could silently violate any of
these and nothing would catch it before quality-eval/security-audit. This
script makes those checks deterministic, per CLAUDE.md's own
"deterministic-first" principle: where a script can decide pass/fail
mechanically, a script decides it, not a model's judgment call.

Usage:
    python validate_skill.py <path/to/skills/skill_id>

Exit 0 = valid, exit 1 = one or more violations (all printed, not just the
first) -- never a partial/silent pass.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ALLOWED_TOP_LEVEL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_TOP_LEVEL_KEYS = {"name", "description", "license"}
REQUIRED_METADATA_KEYS = {"domain", "task_type", "risk_tier", "source", "elicited_from"}
VALID_RISK_TIERS = {"N1", "N2", "N3", "N4", "N5"}
VALID_TASK_TYPES = {"research", "document-conversion", "drafting", "review-qa", "coordination", "skill-authoring"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_COMPATIBILITY_LEN = 500
MAX_SKILL_MD_LINES = 500


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    """Split SKILL.md into (frontmatter_text, body_text). No YAML dependency
    -- parses just enough of the flat/nested structure Scriptorium actually
    uses (top-level scalar keys + one nested 'metadata:' block of scalar
    key: value pairs), refusing rather than guessing on anything fancier."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    frontmatter = text[3:end].strip("\n\r")
    body_start = text.find("\n", end + 4)
    body = text[body_start + 1:] if body_start != -1 else ""
    return frontmatter, body


def _parse_flat_yaml_block(lines: list[str], indent: int) -> dict[str, str]:
    """Parse a flat block of 'key: value' lines at a fixed indent level.
    Deliberately refuses (raises) on list/multi-line values -- this
    validator only needs to read scalar fields, not fully parse YAML."""
    result: dict[str, str] = {}
    for line in lines:
        if not line.strip():
            continue
        stripped_indent = len(line) - len(line.lstrip(" "))
        if stripped_indent != indent:
            continue
        if ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def parse_frontmatter(frontmatter_text: str) -> tuple[dict[str, str], dict[str, str], set[str]]:
    """Returns (top_level_fields, metadata_fields, all_top_level_keys_seen).
    top_level_fields/metadata_fields hold only scalar values actually parsed
    (allowed-tools lists and other non-scalar values are intentionally not
    captured here -- their presence is still recorded in the key set)."""
    lines = frontmatter_text.split("\n")
    top_keys_seen: set[str] = set()
    top_fields: dict[str, str] = {}
    metadata_lines: list[str] = []
    in_metadata = False
    metadata_indent = None

    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            top_keys_seen.add(key)
            in_metadata = key == "metadata"
            metadata_indent = None
            value = value.strip()
            if value and key != "metadata":
                top_fields[key] = value.strip('"').strip("'")
        elif in_metadata:
            if metadata_indent is None:
                metadata_indent = indent
            metadata_lines.append(line)

    metadata_fields = _parse_flat_yaml_block(metadata_lines, metadata_indent or 2)
    return top_fields, metadata_fields, top_keys_seen


def validate_skill(skill_path: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_path / "SKILL.md"

    if not skill_path.is_dir():
        return [f"'{skill_path}' is not a directory."]
    if not skill_md.exists():
        return [f"{skill_md} not found."]

    raw = skill_md.read_text(encoding="utf-8")
    line_count = raw.count("\n") + 1
    if line_count > MAX_SKILL_MD_LINES:
        errors.append(f"SKILL.md has {line_count} lines, exceeds the {MAX_SKILL_MD_LINES}-line cap.")

    split = _split_frontmatter(raw)
    if split is None:
        errors.append("No valid '---' delimited YAML frontmatter found at the top of SKILL.md.")
        return errors
    frontmatter_text, _body = split

    top_fields, metadata_fields, top_keys_seen = parse_frontmatter(frontmatter_text)

    unexpected = top_keys_seen - ALLOWED_TOP_LEVEL_KEYS
    if unexpected:
        errors.append(
            f"Unexpected top-level frontmatter key(s): {', '.join(sorted(unexpected))}. "
            f"Scriptorium-specific fields must live inside 'metadata', never at top level "
            f"(agentskills.io 6-field spec, CLAUDE.md principle 1)."
        )

    missing_top = REQUIRED_TOP_LEVEL_KEYS - top_keys_seen
    if missing_top:
        errors.append(f"Missing required top-level field(s): {', '.join(sorted(missing_top))}.")

    name = top_fields.get("name", "")
    if name:
        if len(name) > MAX_NAME_LEN:
            errors.append(f"'name' is {len(name)} chars, exceeds the {MAX_NAME_LEN}-char cap.")
        if not NAME_RE.match(name):
            errors.append(f"'name' ({name!r}) must be lowercase letters/digits/hyphens only, no leading/trailing/double hyphens.")
        if name != skill_path.name:
            errors.append(f"'name' ({name!r}) does not match the parent folder name ({skill_path.name!r}).")
    elif "name" in top_keys_seen:
        errors.append("'name' is present but empty.")

    description = top_fields.get("description", "")
    if description:
        if len(description) > MAX_DESCRIPTION_LEN:
            errors.append(f"'description' is {len(description)} chars, exceeds the {MAX_DESCRIPTION_LEN}-char cap.")
        if "<" in description or ">" in description:
            errors.append("'description' contains angle brackets ('<' or '>'), not allowed.")
    elif "description" in top_keys_seen:
        errors.append("'description' is present but empty.")

    compatibility = top_fields.get("compatibility", "")
    if compatibility and len(compatibility) > MAX_COMPATIBILITY_LEN:
        errors.append(f"'compatibility' is {len(compatibility)} chars, exceeds the {MAX_COMPATIBILITY_LEN}-char cap.")

    if "metadata" not in top_keys_seen:
        errors.append("Missing 'metadata' block.")
    else:
        missing_meta = REQUIRED_METADATA_KEYS - set(metadata_fields.keys())
        if missing_meta:
            errors.append(f"Missing required metadata field(s): {', '.join(sorted(missing_meta))}.")

        elicited_from = metadata_fields.get("elicited_from", "")
        if "elicited_from" in metadata_fields and not elicited_from:
            errors.append(
                "'metadata.elicited_from' is present but empty -- must name a real elicited source "
                "(CLAUDE.md principle 4: never let a skill be self-generated without elicitation)."
            )

        risk_tier = metadata_fields.get("risk_tier", "")
        if risk_tier and risk_tier not in VALID_RISK_TIERS:
            errors.append(f"'metadata.risk_tier' ({risk_tier!r}) must be one of {sorted(VALID_RISK_TIERS)}.")

        task_type = metadata_fields.get("task_type", "")
        if task_type and task_type not in VALID_TASK_TYPES:
            errors.append(
                f"'metadata.task_type' ({task_type!r}) is not one of the recognized values "
                f"{sorted(VALID_TASK_TYPES)} -- if this is deliberate, double check against "
                f"registry/SCHEMA.md before proceeding."
            )

        source = metadata_fields.get("source", "")
        if source and source not in {"self-authored", "harvested"}:
            errors.append(f"'metadata.source' ({source!r}) must be 'self-authored' or 'harvested'.")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_skill.py <path/to/skills/skill_id>", file=sys.stderr)
        return 2

    skill_path = Path(sys.argv[1])
    errors = validate_skill(skill_path)

    if errors:
        print(f"INVALID: {skill_path} -- {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {skill_path} passes structural validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
