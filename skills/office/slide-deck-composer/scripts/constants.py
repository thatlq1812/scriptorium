"""
Core EMU/layout constants for the slide-deck-composer engine.

Ported (data, not code shape) from two independently-duplicated real
constant modules in the source platform:
  D:/elix/archive/platform_archive/modules/presentation/pptx/constants.py
  D:/elix/archive/platform_archive/modules/presentation/ooxml/constants.py
Both defined the same real EMU/16:9-widescreen values; this module is
the single clean merge for this skill.
"""
from __future__ import annotations

# =============================================================================
# UNIT CONVERSIONS
# =============================================================================

EMU_PER_INCH = 914400
EMU_PER_PT = 12700
EMU_PER_CM = 360000

# Standard 16:9 slide dimensions (13.333" x 7.5")
SLIDE_WIDTH_EMU = 12192000
SLIDE_HEIGHT_EMU = 6858000


def pt_to_emu(pt: float) -> int:
    return int(pt * EMU_PER_PT)


def emu_to_pt(emu: int) -> float:
    return emu / EMU_PER_PT


def inches_to_emu(inches: float) -> int:
    return int(inches * EMU_PER_INCH)


# =============================================================================
# LAYOUT TYPES (v1 - 6 prioritized layouts only, see SKILL.md "Known
# limitations" for the ~14 layout types NOT implemented in this pass)
# =============================================================================

LAYOUT_TITLE = "LAYOUT_TITLE"      # cover/title slide
LAYOUT_STD = "LAYOUT_STD"          # standard bullets slide
LAYOUT_2COL = "LAYOUT_2COL"        # two-column comparison
LAYOUT_IMG = "LAYOUT_IMG"          # image + caption/text
LAYOUT_QUOTE = "LAYOUT_QUOTE"      # centered quote/statement
LAYOUT_SECTION = "LAYOUT_SECTION"  # section divider
LAYOUT_CUSTOM = "LAYOUT_CUSTOM"    # caller-declared ad-hoc slot mapping, see SKILL.md "Custom layout"

SUPPORTED_LAYOUTS = frozenset({
    LAYOUT_TITLE, LAYOUT_STD, LAYOUT_2COL, LAYOUT_IMG, LAYOUT_QUOTE, LAYOUT_SECTION,
    LAYOUT_CUSTOM,
})

# Caller-facing layout name -> internal LAYOUT_* constant.
LAYOUT_NAME_MAP: dict[str, str] = {
    "title": LAYOUT_TITLE,
    "standard": LAYOUT_STD,
    "bullets": LAYOUT_STD,
    "two_column": LAYOUT_2COL,
    "image": LAYOUT_IMG,
    "quote": LAYOUT_QUOTE,
    "section": LAYOUT_SECTION,
    "custom": LAYOUT_CUSTOM,
}

# NOT covered by a NAMED layout above, and not a candidate for one
# either (use "custom" instead, see SKILL.md "Custom layout"): three_column,
# table, code, timeline, chart, stat, diagram, pros_cons, steps, qa,
# icon_grid, center_generic, end_card, fullbleed_image. These aren't a
# roadmap of layouts to eventually hardcode one at a time -- "custom"
# is the general answer to all of them, a real named layout only gets
# added when a shape recurs often enough to be worth a purpose-built,
# validated content schema (e.g. "quote" already gets font-size
# balancing, autofit, and a specific 1-slot contract "custom" doesn't).

# =============================================================================
# TEXT CHARACTER LIMITS (heuristic auto-fit)
# =============================================================================

CHAR_LIMITS: dict[str, dict[str, int]] = {
    "title": {"soft": 60, "hard": 90},
    "subtitle": {"soft": 100, "hard": 140},
    "bullet_point": {"soft": 120, "hard": 170},
    "body_text": {"soft": 500, "hard": 700},
    "speaker_notes": {"soft": 1500, "hard": 2000},
}

MAX_BULLETS_PER_SLIDE = 6
MAX_BULLETS_PER_COLUMN = 4

# =============================================================================
# OOXML NAMESPACES
# =============================================================================

OOXML_NS: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
NS_A = f"{{{OOXML_NS['a']}}}"
NS_R = f"{{{OOXML_NS['r']}}}"
NS_P = f"{{{OOXML_NS['p']}}}"
