"""
Content-length-based font-size balancing (new feature 2, thatlq1812-requested).

thatlq1812's exact framing: "content goc 100 chu, ma noi dung moi 200 chu,
thi co the xem xet giam font, nhat la cac title doc lap" (if the
original template placeholder had ~100 chars and the caller's real
content is ~200 chars, consider shrinking the font -- especially for
standalone titles).

Design (deterministic, discrete steps, not continuous scaling):

    ratio = new_char_count / original_char_count

Every +50% over the original length steps the font down one tier:

    steps = floor((ratio - 1.0) / 0.5)   for ratio > 1.0, else 0

Why +50% per step: the OOXML autofit heuristic this engine also enables
(``text_utils.enable_autofit``) already handles the 0-50% overflow band
at PowerPoint-open-time via its own dynamic normAutofit scaling: text
that's up to ~1.5x the original density typically still fits after
PowerPoint's own shrink-to-fit pass. Beyond that, a single normAutofit
pass tends to shrink too aggressively/uniformly and can under-fill the
shape after the user's next edit, so this engine pre-empts it with an
explicit, predictable, discrete step down applied directly to the run's
font.size -- deterministic and testable, matching this project's
"deterministic-first" discipline for physical fit constraints.

Two step tables, applied per-shape-role (title steps are larger because
title overflow is the most visually jarring per thatlq1812's specific
callout; body/bullet steps are smaller and floor higher since dense
body text already reads fine smaller, but going below ~10pt reads as
a rendering bug, not a design choice):

    role=title -> step 4pt per tier, floor 18pt
    role=body  -> step 2pt per tier, floor 10pt

Steps are capped at 4 tiers (a 5th+ tier would push title below the
floor for any starting size <= 34pt, at which point the situation needs
actual content trimming, not more shrinking -- this module does not
silently truncate; that stays text_utils.truncate_text's job upstream).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

_STEP_PT: dict[str, float] = {"title": 4.0, "body": 2.0}
_FLOOR_PT: dict[str, float] = {"title": 18.0, "body": 10.0}
_MAX_STEPS = 4
_RATIO_STEP_UNIT = 0.5  # +50% length per one font-size step


@dataclass(frozen=True)
class FontSizeDecision:
    original_char_count: int
    new_char_count: int
    ratio: float
    steps: int
    original_pt: float
    balanced_pt: float
    applied: bool


def compute_balanced_font_size(
    original_char_count: int,
    new_char_count: int,
    original_pt: float,
    role: str = "title",
) -> FontSizeDecision:
    """
    Compute the font size to use after comparing original vs. new
    content length for a single cloned shape.

    Args:
        original_char_count: Character count of the template's OWN
            placeholder text before it was overwritten (measured on the
            just-cloned real shape, before injection -- see
            compile_deck.py's call site for how this is captured).
        new_char_count: Character count of the caller-supplied
            replacement text that will actually be injected.
        original_pt: The font size (points) the shape would otherwise
            use (either the template's own run size, or this engine's
            already-computed base size for that role).
        role: "title" or "body" -- selects the step/floor table.

    Returns:
        FontSizeDecision with the resolved font size and whether a
        step-down was applied.
    """
    if role not in _STEP_PT:
        role = "body"

    if original_char_count <= 0 or original_pt <= 0:
        # No real baseline to compare against -- do not guess a
        # step-down; keep the original/base size unchanged.
        return FontSizeDecision(
            original_char_count=original_char_count,
            new_char_count=new_char_count,
            ratio=1.0,
            steps=0,
            original_pt=original_pt,
            balanced_pt=original_pt,
            applied=False,
        )

    ratio = new_char_count / original_char_count
    if ratio <= 1.0:
        steps = 0
    else:
        steps = math.floor((ratio - 1.0) / _RATIO_STEP_UNIT)
    steps = max(0, min(steps, _MAX_STEPS))

    step_pt = _STEP_PT[role]
    floor_pt = _FLOOR_PT[role]
    balanced_pt = max(original_pt - steps * step_pt, floor_pt)

    return FontSizeDecision(
        original_char_count=original_char_count,
        new_char_count=new_char_count,
        ratio=ratio,
        steps=steps,
        original_pt=original_pt,
        balanced_pt=balanced_pt,
        applied=steps > 0 and balanced_pt < original_pt,
    )
