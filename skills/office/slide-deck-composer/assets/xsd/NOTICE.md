# Provenance: OOXML (ECMA-376) XSD schemas

These 24 `.xsd` files are the real ECMA-376 PresentationML/DrawingML/
shared-type schema set, copied verbatim (unmodified) from
[`scanny/python-pptx`](https://github.com/scanny/python-pptx)'s own
`lab/parse_xsd/xsd/` directory (fetched 2026-08-02 via the GitHub API).

**Why this source, not the raw ECMA International standard or an
unlicensed GitHub mirror:** `python-pptx` is already this skill's own
core, license-cleared dependency (MIT). Its repository bundles this
exact schema set — same files, same content — under the **same MIT
license** as the rest of the project. A different mirror found during
scouting (`t-yuki/ooxml-xsd`) has no declared license at all and was
deliberately NOT used, per this project's discipline of never
assuming a license, only using what's directly verifiable
(project guidelines principle 3/5).

**License**: MIT (inherited from `python-pptx`, `python-pptx/LICENSE`
at the same commit). Redistribution permitted with the copyright/
license notice retained — this file serves as that notice for this
skill's own copy.

**Used by**: `scripts/validate_deck.py`'s `ooxml_schema_valid` check
(v0.7.0) — validates every `ppt/slides/slideN.xml` part of a compiled
deck against the real `pml.xsd` root schema (which itself
`xsd:include`s/`xsd:import`s the DrawingML and shared-type schemas
also present in this directory) via `lxml.etree.XMLSchema`. No new
dependency — `lxml` is already required by this skill.

**Feasibility confirmed empirically before adoption** (not assumed):
validated 15 real slide XML parts across 3 different real Slidesgo
templates, and 9 slides from this skill's own real compiled output —
all 24 passed clean. Real-world OOXML producers (Slidesgo, Google
Slides exports, this skill's own clone-and-inject engine) do not, in
practice, violate the strict ECMA-376 schema in the samples checked.
