#!/usr/bin/env python3
"""Deterministic validator: checks a content.json cross-references a
layout.json completely -- every zone in the layout has a matching content
entry, and vice versa (catches a typo'd zone id before it silently drops
content or crashes mid-render). No AI call, stdlib only. Same content.json
contract poster-generator (superseded by this skill) used.

CLI:
    python validate_content.py layout.json content.json

Importable:
    from validate_content import validate_content
    errors = validate_content(layout_dict, content_dict, base_dir)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from font_embed import validate_fonts  # noqa: E402

CONTENT_TYPES = ("image", "text", "fill")


def validate_content(layout: dict, content: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []

    if not isinstance(content, dict) or "zones" not in content:
        return ["content.json must be an object with a 'zones' key"]

    if "transparent_background" in content and not isinstance(content["transparent_background"], bool):
        errors.append(f"'transparent_background' must be a boolean if present, got {content['transparent_background']!r}")

    if "fonts" in content:
        errors.extend(validate_fonts(content["fonts"], base_dir))
        declared_families = set(content["fonts"]) if isinstance(content["fonts"], dict) else set()
    else:
        declared_families = set()

    layout_zone_ids = {z["id"] for z in layout.get("zones", []) if isinstance(z, dict) and "id" in z}
    content_zone_ids = set(content["zones"].keys()) if isinstance(content["zones"], dict) else set()

    missing = layout_zone_ids - content_zone_ids
    if missing:
        errors.append(f"content.json is missing entries for layout zone(s): {sorted(missing)}")
    extra = content_zone_ids - layout_zone_ids
    if extra:
        errors.append(f"content.json has entries for zone(s) not in layout.json (typo?): {sorted(extra)}")

    layout_zones_by_id = {z["id"]: z for z in layout.get("zones", []) if isinstance(z, dict) and "id" in z}

    for zone_id, entry in (content.get("zones") or {}).items():
        prefix = f"content.zones['{zone_id}']"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        entry_type = entry.get("type")
        if entry_type not in CONTENT_TYPES:
            errors.append(f"{prefix}.type must be one of {CONTENT_TYPES}, got {entry_type!r}")
            continue

        layout_zone = layout_zones_by_id.get(zone_id)
        if layout_zone and layout_zone.get("type") == "typography_frame" and entry_type != "text":
            errors.append(f"{prefix}: layout zone '{zone_id}' is a typography_frame, content must be type 'text'")
        if layout_zone and layout_zone.get("type") != "typography_frame" and entry_type == "text":
            errors.append(f"{prefix}: layout zone '{zone_id}' is not a typography_frame, content type 'text' is only valid there")

        if entry_type == "image":
            path = entry.get("path")
            if not isinstance(path, str) or not path.strip():
                errors.append(f"{prefix}.path must be a non-empty string")
            else:
                resolved = path if Path(path).is_absolute() else base_dir / path
                if not Path(resolved).is_file():
                    errors.append(f"{prefix}.path does not exist on disk: {resolved}")
            fit = entry.get("fit", "cover")
            if fit not in ("cover", "contain"):
                errors.append(f"{prefix}.fit must be 'cover' or 'contain', got {fit!r}")

        if entry_type == "text":
            text = entry.get("text")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{prefix}.text must be a non-empty string")
            font_family = entry.get("font_family")
            if font_family is not None and font_family not in declared_families:
                errors.append(f"{prefix}.font_family {font_family!r} is not declared in content.json's top-level 'fonts' object (declared: {sorted(declared_families)})")
            color = entry.get("color", "#000000")
            if not isinstance(color, str) or not color.startswith("#"):
                errors.append(f"{prefix}.color must be a hex string like '#222222', got {color!r}")

        if entry_type == "fill":
            color = entry.get("color")
            if not isinstance(color, str) or not color.startswith("#"):
                errors.append(f"{prefix}.color must be a hex string like '#F5E6C8', got {color!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout_path", type=Path)
    parser.add_argument("content_path", type=Path)
    args = parser.parse_args()

    for p in (args.layout_path, args.content_path):
        if not p.is_file():
            sys.exit(f"Not found: {p}")

    layout = json.loads(args.layout_path.read_text(encoding="utf-8"))
    content = json.loads(args.content_path.read_text(encoding="utf-8"))

    errors = validate_content(layout, content, base_dir=args.content_path.parent)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("OK: content.json fully cross-references layout.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
