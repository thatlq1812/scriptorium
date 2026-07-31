"""Real Word-native list numbering for create_docx.py.

python-docx has no high-level API for numbered/bulleted lists — the naive
approach (prefixing paragraph text with a literal "1.", "2.", ...) is not a
real Word list: it doesn't auto-renumber, doesn't use Word's native list
formatting, and breaks the moment a list item is reordered or deleted.

Word numbering is two-layered OOXML, written into the docx's
``word/numbering.xml`` part:

  * ``w:abstractNum`` — the abstract definition (format, level config).
  * ``w:num``          — a concrete instance pointing to an ``abstractNumId``.

Each call to ``register_numbering`` creates a fresh ``abstractNum`` + ``num``
pair with unique IDs, so multiple lists in the same document never collide
and each one restarts its counter at 1 independently (Word ties the running
count to the concrete ``numId``, not the abstract definition).

Adapted from the owner's own prior production system:
``D:/elix/archive/platform_archive/modules/document/v6/renderers/docx/numbering.py``
(ported and simplified for office-doc-creator's flat, single-level list
content spec — no nested sub-lists in this skill's JSON shape).
"""
from __future__ import annotations

from typing import Literal

from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.parts.numbering import NumberingPart
from lxml import etree

# Content-spec format token -> Word ``numFmt`` value. This is the exhaustive
# supported set — anything else must be refused loudly by the caller rather
# than silently degraded to a default.
SUPPORTED_LIST_FORMATS: dict[str, str] = {
    "decimal": "decimal",
    "roman_upper": "upperRoman",
    "roman_lower": "lowerRoman",
    "alpha_upper": "upperLetter",
    "alpha_lower": "lowerLetter",
    "bullet": "bullet",
}

_BULLET_CHAR = "\u2022"  # "•"
_BULLET_FONT = "Symbol"
_LEVEL_INDENT_TWIPS = 360  # 0.25 inch, single level only.

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _ensure_numbering_part(doc: DocxDocument) -> NumberingPart:
    """Return the docx's numbering part, creating it if absent."""
    part = doc.part
    for rel in part.rels.values():
        if rel.reltype.endswith("/numbering"):
            return rel.target_part  # type: ignore[return-value]

    numbering_part = NumberingPart.new()
    part.relate_to(numbering_part, NumberingPart.relationship_type)  # type: ignore[attr-defined]
    return numbering_part


def _next_id(root: etree._Element, tag: str, attr: str, start: int) -> int:
    """Find the lowest unused integer id for elements matching ``tag``/``attr``."""
    used: set[int] = set()
    for el in root.findall(qn(tag)):
        raw = el.get(qn(attr))
        if raw is None:
            continue
        try:
            used.add(int(raw))
        except ValueError:
            continue
    candidate = start
    while candidate in used:
        candidate += 1
    return candidate


def register_numbering(
    doc: DocxDocument,
    kind: Literal["ordered", "unordered"],
    list_format: str,
) -> int:
    """Register a new numbering definition and return the resulting ``numId``.

    Raises ``ValueError`` if ``list_format`` is not in ``SUPPORTED_LIST_FORMATS``
    — refuse loudly rather than silently falling back to a default format.
    """
    if list_format not in SUPPORTED_LIST_FORMATS:
        raise ValueError(
            f"Unsupported list format {list_format!r}. "
            f"Supported: {sorted(SUPPORTED_LIST_FORMATS)}"
        )

    word_fmt = SUPPORTED_LIST_FORMATS[list_format]
    is_bullet = word_fmt == "bullet"

    numbering_part = _ensure_numbering_part(doc)
    root = numbering_part.element  # type: ignore[attr-defined]
    if root.nsmap.get("w") is None:
        new_root = etree.Element(qn("w:numbering"), nsmap={"w": _W_NS})
        for child in list(root):
            new_root.append(child)
        root = new_root
        numbering_part._element = root  # type: ignore[attr-defined]

    abstract_num_id = _next_id(root, "w:abstractNum", "w:abstractNumId", 0)
    num_id = _next_id(root, "w:num", "w:numId", 1)

    abstract_num = etree.Element(qn("w:abstractNum"))
    abstract_num.set(qn("w:abstractNumId"), str(abstract_num_id))

    multi_level = etree.SubElement(abstract_num, qn("w:multiLevelType"))
    multi_level.set(qn("w:val"), "hybridMultilevel")

    lvl = etree.SubElement(abstract_num, qn("w:lvl"))
    lvl.set(qn("w:ilvl"), "0")

    start_el = etree.SubElement(lvl, qn("w:start"))
    start_el.set(qn("w:val"), "1")

    # Every list gets its own numId, so Word's running counter for that
    # numId always starts fresh at 1 — no cross-list restart flag needed.
    restart_el = etree.SubElement(lvl, qn("w:lvlRestart"))
    restart_el.set(qn("w:val"), "0")

    fmt_el = etree.SubElement(lvl, qn("w:numFmt"))
    fmt_el.set(qn("w:val"), word_fmt)

    lvl_text = etree.SubElement(lvl, qn("w:lvlText"))
    lvl_text.set(qn("w:val"), _BULLET_CHAR if is_bullet else "%1.")

    lvl_jc = etree.SubElement(lvl, qn("w:lvlJc"))
    lvl_jc.set(qn("w:val"), "left")

    ppr = etree.SubElement(lvl, qn("w:pPr"))
    ind = etree.SubElement(ppr, qn("w:ind"))
    ind.set(qn("w:left"), str(_LEVEL_INDENT_TWIPS))
    ind.set(qn("w:hanging"), "360")

    if is_bullet:
        rpr = etree.SubElement(lvl, qn("w:rPr"))
        rfonts = etree.SubElement(rpr, qn("w:rFonts"))
        rfonts.set(qn("w:ascii"), _BULLET_FONT)
        rfonts.set(qn("w:hAnsi"), _BULLET_FONT)
        rfonts.set(qn("w:cs"), _BULLET_FONT)
        rfonts.set(qn("w:hint"), "default")

    # Word expects all abstractNum elements before any num element.
    first_num = None
    for child in root:
        if child.tag == qn("w:num"):
            first_num = child
            break
    if first_num is None:
        root.append(abstract_num)
    else:
        first_num.addprevious(abstract_num)

    num = etree.Element(qn("w:num"))
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = etree.SubElement(num, qn("w:abstractNumId"))
    abstract_ref.set(qn("w:val"), str(abstract_num_id))
    root.append(num)

    return num_id


def apply_list_item(paragraph: object, num_id: int, level: int = 0) -> None:
    """Stamp a paragraph with a ``w:numPr`` pointer to ``num_id`` at ``level``."""
    p_el = paragraph._element  # type: ignore[attr-defined]
    p_pr = p_el.get_or_add_pPr()
    for existing in p_pr.findall(qn("w:numPr")):
        p_pr.remove(existing)
    num_pr = etree.SubElement(p_pr, qn("w:numPr"))
    ilvl = etree.SubElement(num_pr, qn("w:ilvl"))
    ilvl.set(qn("w:val"), str(level))
    num_id_el = etree.SubElement(num_pr, qn("w:numId"))
    num_id_el.set(qn("w:val"), str(num_id))


__all__ = ["SUPPORTED_LIST_FORMATS", "apply_list_item", "register_numbering"]
