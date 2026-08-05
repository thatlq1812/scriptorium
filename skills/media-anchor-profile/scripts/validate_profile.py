#!/usr/bin/env python3
"""Deterministic validator for an anchor-profile JSON record (identity/style
reference definition shared by image-generator-gemini, video-generator-gemini,
poster-generator). No AI call, stdlib only.

CLI:
    python validate_profile.py profile.json

Importable:
    from validate_profile import validate_anchor_profile
    errors = validate_anchor_profile(profile_dict, base_dir=profile_path.parent)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STRENGTH_LEVELS = ("strict", "moderate", "loose")
ANCHOR_KEYS = ("identity", "style")


def _validate_anchor_block(name: str, block: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(block, dict):
        return [f"'{name}' must be an object, got {type(block).__name__}"]

    unknown = set(block.keys()) - {"description", "reference_images", "strength"}
    if unknown:
        errors.append(f"'{name}' has unknown key(s): {sorted(unknown)}")

    description = block.get("description")
    reference_images = block.get("reference_images")

    has_description = isinstance(description, str) and description.strip() != ""
    has_refs = isinstance(reference_images, list) and len(reference_images) > 0

    if not has_description and not has_refs:
        errors.append(
            f"'{name}' must have a non-empty 'description' and/or a non-empty 'reference_images' list "
            "-- an anchor block that constrains nothing is not a valid anchor."
        )

    if reference_images is not None:
        if not isinstance(reference_images, list):
            errors.append(f"'{name}.reference_images' must be a list, got {type(reference_images).__name__}")
        else:
            for i, ref in enumerate(reference_images):
                if not isinstance(ref, str) or not ref.strip():
                    errors.append(f"'{name}.reference_images[{i}]' must be a non-empty string path")
                    continue
                ref_path = (base_dir / ref) if not Path(ref).is_absolute() else Path(ref)
                if not ref_path.is_file():
                    errors.append(f"'{name}.reference_images[{i}]' does not exist on disk: {ref_path}")

    strength = block.get("strength", "moderate")
    if strength not in STRENGTH_LEVELS:
        errors.append(f"'{name}.strength' must be one of {STRENGTH_LEVELS}, got {strength!r}")

    return errors


def validate_anchor_profile(profile: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []

    if not isinstance(profile, dict):
        return [f"Profile must be a JSON object, got {type(profile).__name__}"]

    profile_id = profile.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id.strip():
        errors.append("'profile_id' is required and must be a non-empty string")

    present_anchors = [k for k in ANCHOR_KEYS if k in profile]
    if not present_anchors:
        errors.append(f"Profile must declare at least one of {ANCHOR_KEYS} -- an empty profile anchors nothing")

    for key in present_anchors:
        errors.extend(_validate_anchor_block(key, profile[key], base_dir))

    unknown_top = set(profile.keys()) - {"profile_id", *ANCHOR_KEYS}
    if unknown_top:
        errors.append(f"Profile has unknown top-level key(s): {sorted(unknown_top)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_path", type=Path)
    args = parser.parse_args()

    if not args.profile_path.is_file():
        sys.exit(f"Not found: {args.profile_path}")

    try:
        profile = json.loads(args.profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"Invalid JSON in {args.profile_path}: {exc}")

    errors = validate_anchor_profile(profile, base_dir=args.profile_path.parent)
    if errors:
        print(f"INVALID: {args.profile_path} ({len(errors)} error(s))")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {args.profile_path} is a valid anchor profile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
