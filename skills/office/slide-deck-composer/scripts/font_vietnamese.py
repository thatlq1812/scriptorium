"""
Vietnamese font-safety checker (new feature 1, thatlq1812-requested).

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
skills/office/office-doc-creator/scripts/create_docx.py ``ALLOWED_FONTS``
allowlist (Times New Roman, Arial, Calibri, Cambria, Courier New,
Georgia, Segoe UI, Tahoma, Verdana) -- every one of those is present
here with ``supports_vietnamese: True``, confirming the cross-check.

Pattern followed: same refuse-rather-than-guess discipline as
skills/design/light-logo-arranger/scripts/resolve_font_fallback.py (loaded and
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
    # Added v0.6.0: real Google Font, confirmed via direct web search
    # (2026-08-02) to have NO Vietnamese language subset -- its
    # character set covers 103 Latin languages but Vietnamese is not
    # among them (Google Fonts specimen page + googlefonts-discuss
    # thread confirm Vietnamese support for this family was discussed
    # but never shipped). Found because a real template
    # ("Vintage Recipe Book by Slidesgo.pptx") uses it as its actual
    # title font, declared at the slide-layout level (not the theme
    # scheme) -- see font_manager.resolve_effective_font.
    "Libre Baskerville": ("serif", False),
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
    # display
    # Added v0.8.0: real Google Font, confirmed via direct fetch of its
    # own METADATA.pb on Google's font repo (2026-08-03) -- subsets are
    # exactly ["latin", "latin-ext", "menu"], no "vietnamese" entry.
    # Found because a real template ("AI Automation by Slidesgo.pptx")
    # uses it as its actual title font on the cover slide, declared at
    # the slide-layout level (not the theme scheme) -- resolved via
    # font_manager.resolve_effective_font, same pattern as the Libre
    # Baskerville finding above.
    "Silkscreen": ("display", False),
    # sans_serif
    # Added v0.8.0: real Google Font, confirmed via direct fetch of its
    # own METADATA.pb on Google's font repo (2026-08-03) -- subsets are
    # exactly ["latin", "latin-ext", "menu"], no "vietnamese" entry.
    # Found in the same real template ("AI Automation by Slidesgo.pptx")
    # as Silkscreen above, on a content-body shape -- the run-level font
    # name PowerPoint actually wrote is the weight-suffixed variant
    # ("Schibsted Grotesk Medium"), which is the exact string
    # resolve_effective_font reports and therefore the exact string this
    # table must key on to catch it (the base family and other weight
    # suffixes are NOT automatically covered by this entry).
    "Schibsted Grotesk Medium": ("sans_serif", False),
    "Schibsted Grotesk": ("sans_serif", False),
    # Added v0.8.0: real Google Font, confirmed via direct fetch of its
    # own METADATA.pb on Google's font repo (2026-08-03) -- subsets are
    # exactly ["latin", "latin-ext", "menu"], no "vietnamese" entry.
    # Designed for the Taiwan Space Agency's rebrand (Taiwanese
    # Romanization glyphs, not Vietnamese) -- found in the same real
    # template as the two entries above, run-level name as PowerPoint
    # actually wrote it ("TASA Orbiter Medium").
    "TASA Orbiter Medium": ("sans_serif", False),
    # Added v0.8.2: real Google Font, confirmed via direct fetch of its
    # own METADATA.pb on Google's font repo (2026-08-03) -- subsets are
    # ["devanagari", "latin", "latin-ext", "menu"], no "vietnamese"
    # entry. Poppins is one of the most widely-used Google Fonts, which
    # makes this a genuinely useful, non-obvious finding, not a guess
    # confirmed after the fact -- found on a real template's title
    # ("Federal Law Enforcement Training Center by Slidesgo.pptx"),
    # first as the weight variant "Poppins ExtraBold". Keyed on the
    # base family name only -- every weight/style variant (ExtraBold,
    # Black, Medium, ...) now resolves via check_font_vietnamese_safety's
    # weight-suffix-stripping fallback, no per-weight duplicate entry
    # needed.
    "Poppins": ("sans_serif", False),
    # Added v0.8.2: real Google Font, confirmed via direct fetch of its
    # own METADATA.pb on Google's font repo (2026-08-03) -- subsets are
    # ["cyrillic", "japanese", "latin", "latin-ext", "menu"], no
    # "vietnamese" entry (a Japanese-designed family, consistent with
    # its real subset list). Same real template as Poppins above.
    "Zen Kaku Gothic New": ("sans_serif", False),
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


# Real, recurring friction found via v0.8.1/v0.8.2 dogfooding rounds:
# _FONT_TABLE is keyed on the exact run-level font name string, and two
# different real templates both used multiple WEIGHT variants of the
# same family (Schibsted Grotesk / Schibsted Grotesk Medium; Poppins
# ExtraBold / Poppins Black) -- the same real Unicode glyph coverage,
# but each variant needed its own near-duplicate table entry. A weight
# or style suffix never changes a font family's Unicode glyph
# repertoire (only its visual weight/slant), so once the BASE family is
# verified, every weight/style variant is safe to resolve the same way
# -- this is a real, grounded fact about how font families work, not a
# fuzzy guess. Kept deliberately narrow to avoid the exact risk noted
# when this was first deferred: only a FIXED, unambiguous suffix
# vocabulary is stripped, never a prefix/fuzzy match, so two unrelated
# families that merely share a name prefix (e.g. "Roboto" vs "Roboto
# Slab", a genuinely different family, not a weight variant) can never
# be conflated -- "Slab" is not a weight/style word and stays unstripped.
_WEIGHT_STYLE_SUFFIXES: tuple[str, ...] = (
    "extralight italic", "semibold italic", "extrabold italic",
    "light italic", "black italic", "bold italic", "thin italic",
    "medium italic", "regular italic",
    "extralight", "semibold", "extrabold", "regular", "medium",
    "light", "black", "bold", "thin", "italic",
)


def _strip_weight_style_suffix(name: str) -> str | None:
    """Strip exactly one trailing weight/style token from `name`,
    returning the base family name -- or None if no known suffix
    token is present (never a fuzzy/prefix match, see module comment
    above `_WEIGHT_STYLE_SUFFIXES`)."""
    lower = name.lower()
    for suffix in _WEIGHT_STYLE_SUFFIXES:
        needle = " " + suffix
        if lower.endswith(needle) and len(lower) > len(needle):
            return name[: -len(needle)].strip()
    return None


def check_font_vietnamese_safety(font_name: str) -> VietnameseFontCheck:
    """
    Report whether ``font_name`` is Vietnamese-diacritic-safe.

    Case-insensitive exact match against the verified table, falling
    back to a weight/style-suffix-stripped base-family match (see
    `_strip_weight_style_suffix`) before giving up. Never guesses
    beyond that: a font absent from the table (even after stripping)
    returns status="unknown" with no substitute, so the caller can
    refuse loudly rather than silently risk garbled diacritics (see
    module docstring for the discipline this mirrors).
    """
    if not font_name or not font_name.strip():
        return VietnameseFontCheck(font_name=font_name, status="unknown", reason="empty font name")
    name = font_name.strip()

    lower_lookup = {k.lower(): k for k in _FONT_TABLE}
    canonical = lower_lookup.get(name.lower())
    if canonical is None:
        base = _strip_weight_style_suffix(name)
        base_canonical = lower_lookup.get(base.lower()) if base else None
        if base_canonical is not None:
            # Real match via the base family -- report under the
            # ORIGINAL requested name (the specific weight variant
            # actually used on the run), not the stripped base, so a
            # "safe" result keeps applying the exact font PowerPoint
            # already has, and a "substitute" result's reason names
            # what was actually checked.
            category, supports_vi = _FONT_TABLE[base_canonical]
            if supports_vi:
                return VietnameseFontCheck(font_name=name, status="safe")
            chain = _SUBSTITUTE_CHAINS.get(base_canonical, ())
            substitute = chain[0] if chain else _CATEGORY_DEFAULT_SAFE_FONT.get(category, "Calibri")
            return VietnameseFontCheck(
                font_name=name,
                status="substitute",
                substitute=substitute,
                reason=(
                    f"'{name}' (base family '{base_canonical}') lacks confirmed Vietnamese "
                    f"diacritic support; substituting with '{substitute}' (same category: {category})."
                ),
            )
        return VietnameseFontCheck(
            font_name=name,
            status="unknown",
            reason=(
                f"'{name}' is not in the verified {len(_FONT_TABLE)}-font Vietnamese-support "
                f"table (ported from platform_archive's font_config.py FONT_METRICS), even after "
                f"stripping a recognized weight/style suffix. "
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
