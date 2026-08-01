"""
Dimension-based character-capacity estimation for a text shape.

Ported from D:/elix/archive/platform_archive/modules/presentation/
template_import/capacity.py -- a dimension-only heuristic (EMU
measurements), no font-metrics library dependency. Added to this skill
after a real defect found via hands-on visual review (render to JPG,
inspect): shape_roles.score_body_shape previously had no notion of
"how much text can this box actually hold," so a tiny 6-item icon-grid
caption box could outscore a genuinely spacious content placeholder
purely from a placeholder-type bonus. This module gives that scoring a
real, measurable signal instead of a guess.
"""
from __future__ import annotations

# 1 inch = 914400 EMU, 1 pt = 12700 EMU.
EMU_PER_PT = 12700

# Average character width in EMU for common font sizes (empirical,
# Calibri/Arial-class proportional fonts at standard sizes).
_AVG_CHAR_WIDTH_EMU: dict[int, int] = {
    8: 60960, 9: 68580, 10: 76200, 11: 83820, 12: 91440,
    14: 106680, 16: 121920, 18: 137160, 20: 152400,
    24: 182880, 28: 213360, 32: 243840, 36: 274320, 44: 335280,
}

_LINE_HEIGHT_MULTIPLIER = 1.4
_FILL_FACTOR = 0.85  # accounts for margins/padding/wrap overhead


def estimate_character_capacity(width_emu: int, height_emu: int, font_size_pt: float = 14.0) -> int:
    """Estimate how many characters fit inside a shape of this size at
    this font size. Returns 0 for a degenerate/zero-area shape."""
    if width_emu <= 0 or height_emu <= 0:
        return 0

    size_key = int(round(font_size_pt))
    char_width = _AVG_CHAR_WIDTH_EMU.get(size_key)
    if char_width is None:
        # Linear approximation for a size not in the table.
        char_width = max(1, int(size_key * 7620))
    chars_per_line = max(1, width_emu // char_width)

    line_height = int(size_key * EMU_PER_PT * _LINE_HEIGHT_MULTIPLIER)
    num_lines = max(1, height_emu // line_height)

    return int(chars_per_line * num_lines * _FILL_FACTOR)
