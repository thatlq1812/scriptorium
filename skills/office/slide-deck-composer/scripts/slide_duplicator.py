"""
The core clone-and-inject primitive: duplicate a real template slide
(all its shapes, text, images, relationships) into a fresh slide that
is visually byte-identical to the source, ready for text injection.

Ported near-verbatim from the real, pure XML-surgery primitive at
D:/elix/archive/platform_archive/modules/presentation/pptx/compiler.py
(``PPTXCompiler._duplicate_slide`` / ``_strip_template_slides``), which
is the actual mechanism thatlq1812's "clone-and-inject" architecture
decision refers to. Dropped: the ``suppressed_shape_ids`` parameter
(depends on an upstream AI shape-classifier not part of this skill's
scope) - always duplicates the full shape set.
"""
from __future__ import annotations

import logging
from copy import deepcopy

logger = logging.getLogger("slide_deck_composer")

_NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
_NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def duplicate_slide(prs, source_slide):
    """
    Duplicate a slide with all its shapes, text, images, and relationships.

    Creates a fresh slide attached to the same SlideLayout, then
    replaces its spTree with a deep-copied version of the source
    slide's spTree. All slide-level relationships (images, charts,
    hyperlinks, embedded media) are re-attached to the new slide and
    any rId references inside the copied XML are remapped to the new
    relationship ids.

    The new slide is visually byte-identical to the source; only text
    content needs to be replaced afterward via shape_roles scoring +
    rich_text injection.

    Args:
        prs: The Presentation to add the new slide to.
        source_slide: The Slide to duplicate (a REAL slide already in
            the caller-supplied template, not a bare Slide Layout).

    Returns:
        The newly created Slide (appended to the end of prs.slides).
    """
    source_layout = source_slide.slide_layout
    new_slide = prs.slides.add_slide(source_layout)

    new_sp_tree = new_slide.shapes._spTree
    keep_tags = {f"{{{_NS_P}}}nvGrpSpPr", f"{{{_NS_P}}}grpSpPr"}
    for child in list(new_sp_tree):
        if child.tag in keep_tags:
            continue
        new_sp_tree.remove(child)

    rid_map: dict[str, str] = {}
    try:
        source_rels = source_slide.part.rels
    except Exception:
        source_rels = {}

    for old_rid, rel in source_rels.items():
        try:
            if rel.is_external:
                new_rid = new_slide.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
            else:
                new_rid = new_slide.part.relate_to(rel.target_part, rel.reltype)
            rid_map[old_rid] = new_rid
        except Exception as exc:
            logger.debug("duplicate_slide: failed to copy rel %s (%s): %s", old_rid, rel.reltype, exc)

    source_sp_tree = source_slide.shapes._spTree
    rid_attrs = (f"{{{_NS_R}}}id", f"{{{_NS_R}}}embed", f"{{{_NS_R}}}link")

    for child in list(source_sp_tree):
        if child.tag in keep_tags:
            continue
        cloned = deepcopy(child)
        for el in cloned.iter():
            for attr in rid_attrs:
                old_rid = el.get(attr)
                if old_rid and old_rid in rid_map:
                    el.set(attr, rid_map[old_rid])
        new_sp_tree.append(cloned)

    return new_slide


def strip_template_slides(prs, count: int) -> None:
    """
    Remove the first ``count`` slides (the original template slides
    used purely as clone sources) so the final file only contains the
    generated content slides.

    Deletion proceeds in reverse order to keep XML element indices
    stable during iteration.
    """
    sld_id_lst = prs.slides._sldIdLst
    for i in range(count - 1, -1, -1):
        sld_id = sld_id_lst[i]
        r_id = sld_id.get(f"{{{_NS_R}}}id")
        sld_id_lst.remove(sld_id)
        if r_id is not None:
            prs.part.drop_rel(r_id)
    logger.info("Stripped %d original template slide(s); %d content slide(s) remain", count, len(prs.slides))
