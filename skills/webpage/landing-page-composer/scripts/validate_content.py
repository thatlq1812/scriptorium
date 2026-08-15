#!/usr/bin/env python3
"""Validate a landing-page content record's STRUCTURE before rendering --
section types/required fields, design_system token completeness, and the
real convention (confirmed across all 34 patterns in the harvested
landing-page-pattern dataset design-system-recommender bundles) that a
landing page's first section is always a hero. Stdlib only (json), no
network/AI call.

Exit codes: 0 = valid, 1 = issues found, 2 = malformed input (when run standalone).

Usage (standalone):
    python validate_content.py <content.json>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_COLOR_TOKENS = (
    "primary", "on_primary", "secondary", "on_secondary", "accent", "on_accent",
    "background", "foreground", "card", "card_foreground", "muted", "muted_foreground",
    "border", "destructive", "on_destructive", "ring",
)
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def validate_design_system(ds: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(ds, dict):
        return ["design_system must be an object"]

    tokens = ds.get("color_tokens")
    if not isinstance(tokens, dict):
        errors.append("design_system.color_tokens must be an object")
    else:
        for tok in REQUIRED_COLOR_TOKENS:
            val = tokens.get(tok)
            if not isinstance(val, str) or not HEX_RE.match(val):
                errors.append(f"design_system.color_tokens.{tok} must be a '#RRGGBB' hex color, got {val!r}")

    font = ds.get("font_pairing")
    if not isinstance(font, dict):
        errors.append("design_system.font_pairing must be an object")
    else:
        require_nonempty_text(font.get("heading_font"), "design_system.font_pairing.heading_font", errors)
        require_nonempty_text(font.get("body_font"), "design_system.font_pairing.body_font", errors)

    return errors


def validate_hero(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    require_nonempty_text(s.get("headline"), f"{p}.headline", errors)
    require_nonempty_text(s.get("cta_text"), f"{p}.cta_text", errors)
    require_nonempty_text(s.get("cta_href"), f"{p}.cta_href", errors)
    return errors


def validate_features(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    require_nonempty_text(s.get("title"), f"{p}.title", errors)
    items = s.get("items")
    if not isinstance(items, list) or not items:
        errors.append(f"{p}.items must be a non-empty list")
    else:
        for j, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{p}.items[{j}] must be an object")
                continue
            require_nonempty_text(item.get("title"), f"{p}.items[{j}].title", errors)
            require_nonempty_text(item.get("description"), f"{p}.items[{j}].description", errors)
    return errors


def validate_testimonial(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    require_nonempty_text(s.get("quote"), f"{p}.quote", errors)
    require_nonempty_text(s.get("author"), f"{p}.author", errors)
    return errors


def validate_pricing(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    tiers = s.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        errors.append(f"{p}.tiers must be a non-empty list")
    else:
        for j, tier in enumerate(tiers):
            if not isinstance(tier, dict):
                errors.append(f"{p}.tiers[{j}] must be an object")
                continue
            require_nonempty_text(tier.get("name"), f"{p}.tiers[{j}].name", errors)
            require_nonempty_text(tier.get("price"), f"{p}.tiers[{j}].price", errors)
            features = tier.get("features")
            if not isinstance(features, list) or not features:
                errors.append(f"{p}.tiers[{j}].features must be a non-empty list of strings")
    return errors


def validate_cta(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    require_nonempty_text(s.get("headline"), f"{p}.headline", errors)
    require_nonempty_text(s.get("button_text"), f"{p}.button_text", errors)
    require_nonempty_text(s.get("button_href"), f"{p}.button_href", errors)
    return errors


def validate_footer(s: dict, i: int) -> list[str]:
    errors: list[str] = []
    p = f"sections[{i}]"
    require_nonempty_text(s.get("text"), f"{p}.text", errors)
    return errors


SECTION_VALIDATORS = {
    "hero": validate_hero,
    "features": validate_features,
    "testimonial": validate_testimonial,
    "pricing": validate_pricing,
    "cta": validate_cta,
    "footer": validate_footer,
}


def validate_sections(sections: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(sections, list) or not sections:
        return ["sections must be a non-empty list"]

    first = sections[0]
    if not isinstance(first, dict) or first.get("type") != "hero":
        errors.append(
            "sections[0] must be of type 'hero' -- every landing-page pattern in this project's own "
            "reference dataset (34/34 patterns, see design-system-recommender's landing_patterns.json) "
            "starts with a hero section"
        )

    for i, s in enumerate(sections):
        if not isinstance(s, dict):
            errors.append(f"sections[{i}] must be an object")
            continue
        stype = s.get("type")
        validator = SECTION_VALIDATORS.get(stype)
        if validator is None:
            errors.append(f"sections[{i}].type must be one of {sorted(SECTION_VALIDATORS)}, got {stype!r}")
            continue
        errors.extend(validator(s, i))

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    if "design_system" not in record:
        errors.append("design_system key is required")
    else:
        errors.extend(validate_design_system(record.get("design_system")))

    if "sections" not in record:
        errors.append("sections key is required")
    else:
        errors.extend(validate_sections(record.get("sections")))

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_content.py <content.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(data.get('sections', []))} section(s), structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
