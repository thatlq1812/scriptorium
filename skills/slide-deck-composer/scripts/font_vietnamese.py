"""
Vietnamese font-safety checker (new feature 1, owner-requested).

Given a font name (the template's own theme font, or a caller-requested
font-swap target), report:
  - "safe":        confirmed Vietnamese-diacritic support, use as-is.
  - "substitute":  confirmed to LACK Vietnamese support; a real,
                    same-category substitute is returned.
  - "unknown":      no data for this font. Refuses loudly rather than
                    guessing (same discipline as light-logo-arranger's
                    resolve_font_fallback.py -- see below).

Data source: ported verbatim (real, measured data -- not invented) from
D:/elix/archive/platform_archive/modules/presentation/layout_registry/font_config.py's
``FONT_METRICS`` table (35 fonts, each with a directly-set
``supports_vietnamese`` bool) and cross-checked against
D:/elix/archive/platform_archive/modules/presentation/template_factory/font_pairing.py's
``VIETNAMESE_SAFE_FONTS`` list (both agree on every font they share).
Also cross-checked against this project's own
skills/office-doc-creator/scripts/create_docx.py ``ALLOWED_FONTS``
allowlist (Times New Roman, Arial, Calibri, Cambria, Courier New,
Georgia, Segoe UI, Tahoma, Verdana) -- every one of those is present
here with ``supports_vietnamese: True``, confirming the cross-check.

Pattern followed: same refuse-rather-than-guess discipline as
skills/light-logo-arranger/scripts/resolve_font_fallback.py (loaded and
reviewed as part of this build) -- an unmapped font is refused, never
silently assumed vietnamese-safe or silently substituted.
"""
from __future__ import annotations

from dataclasses import dataclass

# Each entry: (category, supports_vietnamese).
# Source: platform_archive/modules/presentation/layout_registry/font_config.py
# FONT_METRICS (35 fonts, real measured/verified table).
_FONT_TABLE: dict[str, tuple[str, bool]] = {
    # sans-serif
    "Calibri": ("sans_serif", True),
    "Arial": ("sans_serif", True),
    "Helvetica": ("sans_serif", True),
    "Segoe UI": ("sans_serif", True),
    "Tahoma": ("sans_serif", True),
    "Verdana": ("sans_serif", True),
    "Roboto": ("sans_serif", True),
    "Open Sans": ("sans_serif", True),
    "Lato": ("sans_serif", True),
    "Montserrat": ("sans_serif", True),
    "Poppins": ("sans_serif", True),
    "Nunito": ("sans_serif", True),
    "Inter": ("sans_serif", True),
    "Source Sans Pro": ("sans_serif", True),
    "Noto Sans": ("sans_serif", True),
    # serif
    "Times New Roman": ("serif", True),
    "Georgia": ("serif", True),
    "Garamond": ("serif", False),
    "Palatino Linotype": ("serif", True),
    "Cambria": ("serif", True),
    "Noto Serif": ("serif", True),
    "Playfair Display": ("serif", True),
    "Merriweather": ("serif", True),
    # monospace
    "Consolas": ("monospace", True),
    "Courier New": ("monospace", True),
    "Fira Code": ("monospace", True),
    "Source Code Pro": ("monospace", True),
    "JetBrains Mono": ("monospace", True),
    # display
    "Impact": ("display", True),
    "Comic Sans MS": ("display", True),
    # CJK (kept for negative-case coverage; these lack Vietnamese diacritics)
    "Noto Sans CJK": ("sans_serif", True),
    "MS Gothic": ("sans_serif", False),
    "SimSun": ("serif", False),
    "Malgun Gothic": ("sans_serif", False),
    # handwriting
    "Dancing Script": ("handwriting", True),
}

# Same-category, supports_vietnamese=True substitutes, ranked best-first.
# Ported from FONT_FALLBACKS chains in the same source file, filtered to
# entries this table's category already agrees are vietnamese-safe.
_SUBSTITUTE_CHAINS: dict[str, tuple[str, ...]] = {
    "Garamond": ("Palatino Linotype", "Times New Roman", "Cambria"),
    "MS Gothic": ("Noto Sans CJK", "Segoe UI", "Arial"),
    "SimSun": ("Noto Serif", "Times New Roman", "Georgia"),
    "Malgun Gothic": ("Noto Sans CJK", "Segoe UI", "Arial"),
}

_CATEGORY_DEFAULT_SAFE_FONT: dict[str, str] = {
    "sans_serif": "Calibri",
    "serif": "Times New Roman",
    "monospace": "Consolas",
    "display": "Comic Sans MS",
    "handwriting": "Dancing Script",
}


@dataclass(frozen=True)
class VietnameseFontCheck:
    font_name: str
    status: str  # "safe" | "substitute" | "unknown"
    substitute: str | None = None
    reason: str = ""


def check_font_vietnamese_safety(font_name: str) -> VietnameseFontCheck:
    """
    Report whether ``font_name`` is Vietnamese-diacritic-safe.

    Case-insensitive exact match against the verified table. Never
    guesses: a font absent from the table returns status="unknown" with
    no substitute, so the caller can refuse loudly rather than silently
    risk garbled diacritics (see module docstring for the discipline
    this mirrors).
    """
    if not font_name or not font_name.strip():
        return VietnameseFontCheck(font_name=font_name, status="unknown", reason="empty font name")
    name = font_name.strip()

    lower_lookup = {k.lower(): k for k in _FONT_TABLE}
    canonical = lower_lookup.get(name.lower())
    if canonical is None:
        return VietnameseFontCheck(
            font_name=name,
            status="unknown",
            reason=(
                f"'{name}' is not in the verified {len(_FONT_TABLE)}-font Vietnamese-support "
                f"table (ported from platform_archive's font_config.py FONT_METRICS). "
                f"Refusing to guess -- verify the font's Vietnamese glyph coverage manually "
                f"and add it to _FONT_TABLE in font_vietnamese.py before using it for "
                f"Vietnamese content."
            ),
        )

    category, supports_vi = _FONT_TABLE[canonical]
    if supports_vi:
        return VietnameseFontCheck(font_name=canonical, status="safe")

    chain = _SUBSTITUTE_CHAINS.get(canonical, ())
    substitute = chain[0] if chain else _CATEGORY_DEFAULT_SAFE_FONT.get(category, "Calibri")
    return VietnameseFontCheck(
        font_name=canonical,
        status="substitute",
        substitute=substitute,
        reason=f"'{canonical}' lacks confirmed Vietnamese diacritic support; substituting with '{substitute}' (same category: {category}).",
    )


def resolve_vietnamese_safe_font(font_name: str, *, strict: bool = True) -> str:
    """
    Return a Vietnamese-safe font name to actually use.

    - "safe" -> returns font_name unchanged.
    - "substitute" -> returns the substitute.
    - "unknown" -> raises ValueError when strict=True (default; refuse
      loudly), or returns the category-agnostic default 'Calibri' when
      strict=False (only for non-Vietnamese-content code paths that
      still want a best-effort call).
    """
    check = check_font_vietnamese_safety(font_name)
    if check.status == "safe":
        return check.font_name
    if check.status == "substitute":
        return check.substitute  # type: ignore[return-value]
    if strict:
        raise ValueError(check.reason)
    return "Calibri"
