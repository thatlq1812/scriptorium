"""
Opt-in theme-font override (write path). Default behavior of the
compiler is to leave the template's own theme fonts untouched; this
module is only invoked when the caller explicitly requests a font
swap (``--heading-font`` / ``--body-font`` on compile_deck.py).

Ported and trimmed (pure XML mutation, no I/O beyond the already-open
Presentation) from:
D:/elix/archive/platform_archive/modules/presentation/pptx/font_engine.py
Dropped: apply_font_pack's force-override-every-run path and its
Google-Fonts-embedding integration (network I/O, out of scope) - kept
only ``set_theme_fonts``, which mutates the theme XML's font scheme
(what every unstyled run inherits).
"""
from __future__ import annotations

import logging

from lxml import etree

from constants import OOXML_NS

logger = logging.getLogger("slide_deck_composer")


def set_theme_fonts(
    prs,
    heading_font: str,
    body_font: str,
    heading_ea: str | None = None,
    body_ea: str | None = None,
) -> int:
    """
    Override theme fonts across ALL slide master theme parts.

    Modifies a:fontScheme > a:majorFont/a:minorFont > a:latin[@typeface]
    (and optionally a:ea[@typeface]). python-pptx exposes theme parts as
    plain binary Part objects with no attached _element, so the XML blob
    is parsed, mutated, and re-serialized back via the part's ``blob``
    setter - mutating the parsed etree alone yields a detached copy that
    is never serialized on save.

    Returns:
        Number of theme parts updated.
    """
    ns = OOXML_NS["a"]
    theme_parts = list(_iter_theme_parts(prs))
    if not theme_parts:
        logger.warning("Cannot set theme fonts: no theme parts found")
        return 0

    updated = 0
    for theme_part in theme_parts:
        try:
            root = etree.fromstring(theme_part.blob)
        except etree.XMLSyntaxError as exc:
            logger.warning("Skipping unreadable theme part: %s", exc)
            continue

        font_scheme = root.find(f".//{{{ns}}}fontScheme")
        if font_scheme is None:
            continue

        _update_font_role(font_scheme, "majorFont", heading_font, heading_ea, ns)
        _update_font_role(font_scheme, "minorFont", body_font, body_ea, ns)

        theme_part.blob = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )
        updated += 1

    logger.info("Theme fonts set -- heading: '%s', body: '%s' (%d theme part(s))", heading_font, body_font, updated)
    return updated


def _update_font_role(font_scheme, role_tag: str, latin: str, ea: str | None, ns: str) -> None:
    role_node = font_scheme.find(f"{{{ns}}}{role_tag}")
    if role_node is None:
        return
    latin_node = role_node.find(f"{{{ns}}}latin")
    if latin_node is None:
        latin_node = etree.SubElement(role_node, f"{{{ns}}}latin")
    latin_node.set("typeface", latin)
    if ea:
        ea_node = role_node.find(f"{{{ns}}}ea")
        if ea_node is None:
            ea_node = etree.SubElement(role_node, f"{{{ns}}}ea")
        ea_node.set("typeface", ea)


def _iter_theme_parts(prs):
    seen_partnames = set()
    for slide_master in prs.slide_masters:
        try:
            theme_part = slide_master.part.theme_part
        except AttributeError:
            theme_part = None
        if theme_part is None:
            try:
                for rel in slide_master.part.rels.values():
                    if "theme" in rel.reltype.lower():
                        theme_part = rel.target_part
                        break
            except Exception:
                theme_part = None
        if theme_part is None:
            continue
        partname = str(getattr(theme_part, "partname", id(theme_part)))
        if partname in seen_partnames:
            continue
        seen_partnames.add(partname)
        yield theme_part
