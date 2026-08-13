#!/usr/bin/env python3
"""Validate a home study-environment record (a parent/guardian's setup for
a child's home study: dedicated space, routine, screen-time policy) for
structural completeness, and print advisory (non-blocking) comparisons
against real, cited public parenting/education guidance. Stdlib only
(json, re, argparse), local, deterministic -- no AI/network of any kind.

This does NOT invent numeric thresholds. Every numeric comparison in the
advisory section below is a direct restatement of a real, named public
source (see "Grounding" in SKILL.md for exact citations):

  - Screen-time bands for ages under 18 months and 2-5 years: American
    Academy of Pediatrics (AAP), "Media and Young Minds" (Pediatrics,
    2016) and the AAP's 2026 updated screen-time guidance (aap.org /
    healthychildren.org Family Media Use Plan) -- avoid screens other than
    video-chatting under 18 months; at most ~1 hour/day of high-quality
    content for ages 2-5. The AAP's 2026 update deliberately moved away
    from a single fixed-hours number for ages 6+ toward an individualized
    family media plan -- this script does NOT invent a replacement number
    for that age range; no screen-hours advisory fires for age > 5.
  - Device-free bedroom/mealtime: AAP Family Media Use Plan guidance
    (screens should not displace sleep, physical activity, family time;
    device-free bedrooms and mealtimes support that).
  - Sleep-duration ranges by age: National Sleep Foundation, "How Much
    Sleep Do Babies and Kids Need" (sleepfoundation.org / thensf.org).

Every advisory is a WARNING (printed, non-blocking) -- age-specific human
circumstances vary and this script does not have authority to declare a
family's setup invalid over an advisory number. Structural completeness
checks (below) are the only thing that can produce a hard error.

Checks (errors -- hard-block):
  - child_name non-empty string.
  - study_space: location non-empty string, has_dedicated_desk_or_table
    boolean, distraction_controls a non-empty list of non-empty strings.
  - routine: study_schedule non-empty string. regular_bedtime/
    regular_wake_time, if present, must be valid 24h "HH:MM".
  - screen_time_policy: study_block_device_free, device_free_bedroom,
    device_free_mealtime all required booleans.
    recreational_screen_hours_per_day, if present, must be a non-negative
    number.
  - child_age_years, if present, must be a non-negative number.

Exit codes: 0 = structurally valid (advisories may still print), 1 = at
least one structural error, 2 = file not readable / malformed JSON.

Usage:
    python validate_home_study_environment.py record.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# National Sleep Foundation age-band sleep-duration ranges, in hours,
# keyed by an upper-bound age in years (source: sleepfoundation.org /
# thensf.org "How Much Sleep Do Babies and Kids Need"). Looked up by the
# first band whose upper bound the child's age does not exceed.
NSF_SLEEP_BANDS = [
    (0.25, "0-3 months", 14.0, 17.0),
    (1.0, "4-11 months", 12.0, 15.0),
    (2.0, "1-2 years", 11.0, 14.0),
    (5.0, "3-5 years", 10.0, 13.0),
    (13.0, "6-13 years", 9.0, 11.0),
    (17.0, "14-17 years", 8.0, 10.0),
]


class RecordError(Exception):
    pass


def _require_bool(container: dict, key: str, path: str, errors: list[str]) -> None:
    if key not in container:
        errors.append(f"{path}.{key} is required")
        return
    value = container[key]
    if not isinstance(value, bool):
        errors.append(f"{path}.{key} must be a boolean (true/false), got {type(value).__name__}")


def _require_nonempty_str(container: dict, key: str, path: str, errors: list[str]) -> None:
    if key not in container:
        errors.append(f"{path}.{key} is required")
        return
    value = container[key]
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} must be a non-empty string")


def _parse_time(value: str) -> tuple[int, int] | None:
    m = TIME_RE.match(value)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _sleep_hours(bedtime: tuple[int, int], wake: tuple[int, int]) -> float:
    bed_minutes = bedtime[0] * 60 + bedtime[1]
    wake_minutes = wake[0] * 60 + wake[1]
    delta = wake_minutes - bed_minutes
    if delta <= 0:
        delta += 24 * 60
    return delta / 60.0


def _nsf_band_for_age(age_years: float) -> tuple[str, float, float] | None:
    for upper, label, lo, hi in NSF_SLEEP_BANDS:
        if age_years <= upper:
            return label, lo, hi
    return None  # 18+ not covered by this table -- no advisory fires


def validate(record: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("child_name", "study_space", "routine", "screen_time_policy"):
        if field not in record:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    child_name = record["child_name"]
    if not isinstance(child_name, str) or not child_name.strip():
        errors.append("child_name must be a non-empty string")

    age = record.get("child_age_years")
    if age is not None:
        if not isinstance(age, (int, float)) or isinstance(age, bool) or age < 0:
            errors.append(f"child_age_years must be a non-negative number if present, got {age!r}")
            age = None

    study_space = record["study_space"]
    if not isinstance(study_space, dict):
        errors.append("study_space must be an object")
        study_space = {}
    else:
        _require_nonempty_str(study_space, "location", "study_space", errors)
        _require_bool(study_space, "has_dedicated_desk_or_table", "study_space", errors)
        dc = study_space.get("distraction_controls")
        if "distraction_controls" not in study_space:
            errors.append("study_space.distraction_controls is required")
        elif not isinstance(dc, list) or not dc:
            errors.append("study_space.distraction_controls must be a non-empty list")
        else:
            for i, item in enumerate(dc):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"study_space.distraction_controls[{i}] must be a non-empty string")

    routine = record["routine"]
    bedtime = wake_time = None
    if not isinstance(routine, dict):
        errors.append("routine must be an object")
        routine = {}
    else:
        _require_nonempty_str(routine, "study_schedule", "routine", errors)
        for key in ("regular_bedtime", "regular_wake_time"):
            if key in routine and routine[key] not in (None, ""):
                value = routine[key]
                if not isinstance(value, str) or not _parse_time(value):
                    errors.append(f"routine.{key} must be a valid 24h 'HH:MM' string if present, got {value!r}")
        bedtime = _parse_time(routine["regular_bedtime"]) if isinstance(routine.get("regular_bedtime"), str) else None
        wake_time = _parse_time(routine["regular_wake_time"]) if isinstance(routine.get("regular_wake_time"), str) else None

    screen_policy = record["screen_time_policy"]
    recreational_hours = None
    if not isinstance(screen_policy, dict):
        errors.append("screen_time_policy must be an object")
        screen_policy = {}
    else:
        _require_bool(screen_policy, "study_block_device_free", "screen_time_policy", errors)
        _require_bool(screen_policy, "device_free_bedroom", "screen_time_policy", errors)
        _require_bool(screen_policy, "device_free_mealtime", "screen_time_policy", errors)
        if "recreational_screen_hours_per_day" in screen_policy and screen_policy["recreational_screen_hours_per_day"] is not None:
            recreational_hours = screen_policy["recreational_screen_hours_per_day"]
            if not isinstance(recreational_hours, (int, float)) or isinstance(recreational_hours, bool) or recreational_hours < 0:
                errors.append(f"screen_time_policy.recreational_screen_hours_per_day must be a non-negative number if present, got {recreational_hours!r}")
                recreational_hours = None

    if errors:
        return errors, warnings

    # --- Advisory (non-blocking) checks against cited public guidance ---

    if age is not None and recreational_hours is not None:
        if age < 1.5 and recreational_hours > 0:
            warnings.append(
                f"child_age_years={age}: AAP guidance (Media and Young Minds, 2016; AAP Family Media Use "
                f"Plan) recommends avoiding screen use other than video-chatting for children under 18 "
                f"months -- recreational_screen_hours_per_day is {recreational_hours}, not 0"
            )
        elif 2.0 <= age <= 5.0 and recreational_hours > 1.0:
            warnings.append(
                f"child_age_years={age}: AAP guidance recommends at most about 1 hour/day of "
                f"high-quality content for ages 2-5 -- recreational_screen_hours_per_day is "
                f"{recreational_hours}, above that reference"
            )

    if not screen_policy.get("device_free_bedroom", True):
        warnings.append(
            "screen_time_policy.device_free_bedroom is false -- AAP Family Media Use Plan guidance "
            "recommends keeping bedrooms device-free to protect sleep"
        )
    if not screen_policy.get("device_free_mealtime", True):
        warnings.append(
            "screen_time_policy.device_free_mealtime is false -- AAP Family Media Use Plan guidance "
            "recommends keeping mealtimes device-free for family time"
        )

    if age is not None and bedtime and wake_time:
        band = _nsf_band_for_age(age)
        if band is not None:
            label, lo, hi = band
            actual = round(_sleep_hours(bedtime, wake_time), 1)
            if not (lo <= actual <= hi):
                warnings.append(
                    f"child_age_years={age} (National Sleep Foundation band '{label}', recommended "
                    f"{lo}-{hi}h/night): computed sleep window from regular_bedtime/regular_wake_time "
                    f"is {actual}h, outside that range"
                )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a home study-environment JSON record (see assets/home_study_environment_template.json)")
    args = parser.parse_args()

    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(record, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(record)

    if warnings:
        print(f"ADVISORIES: {len(warnings)} (non-blocking, grounded in cited public guidance -- see script docstring / SKILL.md)")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: study_space/routine/screen_time_policy structurally complete. This confirms structural completeness only -- read any advisories above, they're grounded reference points, not enforced rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
