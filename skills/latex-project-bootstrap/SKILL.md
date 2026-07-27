---
name: latex-project-bootstrap
description: Scaffolds a LaTeX project (book/report) correctly from the start — XeLaTeX + fontspec/polyglossia for Vietnamese, biblatex + biber for bibliography, plus a build script in the correct 4-pass order. Also renders real Vietnamese administrative documents (công văn/quyết định/nghị quyết/biên bản/báo cáo and other tên-loại types) compliant with Nghị định 30/2020/NĐ-CP's real formatting via Typst (not LaTeX — see "Engine per mode"), exportable to PDF or DOCX (Pandoc + a patched reference template, Times New Roman/black, not Pandoc's stock colored-heading default) — no LaTeX or Typst knowledge required. Use when starting a new LaTeX document (book, research report, thesis) containing Vietnamese, OR when a Vietnamese government-style administrative document needs the exact NĐ 30/2020 format, in PDF or DOCX. Do NOT use to write actual book/chapter content or the substantive text of an administrative document — this skill only scaffolds/renders, never invents wording.
license: MIT
compatibility: Book/report scaffold requires XeLaTeX (`xelatex`) + `biber` (MiKTeX/TeX Live, see `xelatex-bootstrap`). vnnd30 mode requires Typst (see `typst-bootstrap` — a single ~50MB static binary, NOT the same toolchain). DOCX export additionally requires `pandoc` on PATH. All scripts are pure Python 3 stdlib, no venv needed. Verified running clean: Claude Code, Windows (2026-07-26, 2026-07-27). See "Verified" section below for real test-case detail.
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in the owner's real LaTeX project (D:/elix/researches/textbooks — a textbook program in real production use): the XeLaTeX + polyglossia/fontspec engine, the xelatex->biber->xelatex->xelatex build sequence, observed directly from textbooks/templates/core/elix-textbook.cls and docs/methodology/idea_to_book_series.md Phase 6. Wrote a generic scaffold from scratch, didn't copy the owner's 476-line .cls file specific to their K-12 program. vnnd30 mode elicited from the real Nghị định 30/2020/NĐ-CP PDF itself (downloaded directly from vanban.chinhphu.vn 2026-07-27, not a secondary source) -- see references/nd30-2020-formatting.md. v0.3.0's DOCX reference-doc patch recipe (not code) adapted from a real, working fix in a sibling project, D:/elix/praxis_csc/resources/templates/reference-vn.docx. v0.4.0's engine switch (XeLaTeX -> Typst for vnnd30 mode only): owner directed this after comparing praxis_csc's own docs/CHANGELOG.md, which records that project independently making the identical switch (Typst replacing xelatex/pdflatex/MiKTeX/TeX Live) for the same portability reason -- a ~5GB TeX distribution isn't realistically bundleable/portable, a ~50MB static Typst binary is."
  version: 0.4.0
  changelog_0_4_0: "Owner-directed architecture change: vnnd30 mode's rendering engine switched from XeLaTeX to Typst, while the book/report scaffold mode (the skill's original purpose, grounded in a real production LaTeX project) stays on XeLaTeX -- see 'Engine per mode' below for why these are deliberately different, not an oversight. assets/vnnd30.sty (LaTeX) replaced by assets/vnnd30.typ (Typst) -- same function set, same font/size/style values, ported not just translated (Typst's own layout primitives, e.g. grid() for the 2-column header instead of LaTeX minipages, and no LaTeX-style paragraph-glue bugs -- Typst's block-based layout doesn't need explicit \\par between sections the way LaTeX does). scripts/render_nd30_document.py rewritten to emit a .typ file + compile via a single `typst compile` pass (not XeLaTeX's 2-pass loop -- Typst resolves page-number references within one compilation). New dependency skill typst-bootstrap (detect + download-a-static-binary, not a system package manager install like xelatex-bootstrap) -- installed and verified for real on this machine (typst 0.15.1). New typst_escape() is narrower than the old latex_escape() (only backslash/double-quote need escaping inside a Typst string literal, vs LaTeX's ~9 special characters) -- verified real against the same &%#_ stress test plus literal quotes/asterisks/underscores, all displayed literally with zero markup injection. Content JSON schema (validate()) is UNCHANGED -- this is a rendering-backend swap, not a schema change. All 5 example content JSONs re-verified: rendered + compiled to real PDF via `typst compile`, visually inspected page by page, functionally identical output to the retired LaTeX version (plus no page-1-suppressed/page-2-shown numbering bug to work around, since Typst's `context`-based page counter just works). export_nd30_docx.py is UNCHANGED (already Markdown-mediated via Pandoc, never depended on the LaTeX engine)."
---

# latex-project-bootstrap

Scaffolds a LaTeX project correctly on the first try — avoiding the 2 most common mistakes someone makes starting on their own: using the wrong engine for Vietnamese, and forgetting the 4-pass build order when a bibliography is involved. Also renders real Vietnamese administrative documents compliant with Nghị định 30/2020/NĐ-CP (vnnd30 mode) — a functionally separate capability that happens to live in the same skill folder; see "Engine per mode" for why it uses a different engine than the name implies.

## Engine per mode — read this before assuming "latex-project-bootstrap" means everything here uses LaTeX

This skill's name reflects its original purpose (the book/report scaffold). It has 2 independent rendering paths, deliberately on 2 different engines:

| Mode | Engine | Why |
| --- | --- | --- |
| Book/report scaffold (`scripts/init_project.py`) | **XeLaTeX** + biblatex/biber | Grounded in the owner's real, already-deployed LaTeX production project (`D:/elix/researches/textbooks`) — that project assumes a full TeX distribution, bibliography management via biber, and the standard academic-publishing toolchain. Switching this to Typst would gain nothing (a full TeX install is already assumed here) and would break consistency with the real system this mode mirrors. |
| Administrative document (vnnd30, `scripts/render_nd30_document.py` + `scripts/export_nd30_docx.py`) | **Typst** for PDF, Pandoc for DOCX | A single fixed-layout document, no bibliography, no table of contents — exactly the case where portability matters more than LaTeX's deeper customization. A full TeX distribution is ~5GB and not realistically bundleable to an arbitrary target machine; Typst is a single ~50MB static binary. A sibling project (`D:/elix/praxis_csc`) independently made the identical switch for its own document-export feature, for the identical reason — see that project's `docs/CHANGELOG.md`. |

Practical consequence: `xelatex-bootstrap` is the dependency for the book/report scaffold; `typst-bootstrap` is the dependency for vnnd30 mode. They are not interchangeable and neither mode needs the other's toolchain.

## Source lesson (from a real LaTeX project)

Read `references/vietnamese-latex-setup.md` before writing a single `.tex` file — a lesson drawn from a real production LaTeX program (not theory): pdfLaTeX + babel `vietnamese` is prone to tone-mark bugs when paired with modern fonts; XeLaTeX + `fontspec`/`polyglossia` handles Unicode directly, far more stable. (This lesson is specific to the book/report scaffold mode — vnnd30 mode sidesteps the whole question by using Typst, which handles Unicode natively with no engine choice to get wrong.)

## Scaffold the project

```bash
python scripts/init_project.py <output_dir> --title "Document title" --font "Noto Serif"
```

Produces: `main.tex` (a correct XeLaTeX preamble + biblatex/biber), `chapters/01_intro.tex`, a sample `bibliography.bib`, `build.sh`/`build.ps1`.

## Build

```bash
# Unix:
bash build.sh
# Windows PowerShell:
.\build.ps1
```

Required order (see `references/vietnamese-latex-setup.md` for why each step is needed): `xelatex → biber → xelatex → xelatex`. Skipping any pass can produce a PDF missing citations or with a wrong table of contents/page numbers.

## What this skill does NOT do

- Doesn't write actual chapter content — only scaffolds the technical setup (preamble, build script).
- Doesn't install a TeX distribution (MiKTeX/TeX Live) — assumes one is already on the machine for the book/report scaffold mode, check with `xelatex --version` (or run `xelatex-bootstrap`) before using that mode.
- Doesn't use a complex custom class (like the source project's `elix-textbook.cls`, with its own macros for a specific textbook program) — uses the standard `book` class + a minimal preamble, keeping the skill portable for any kind of document, not just textbooks.
- (vnnd30 mode) Doesn't write the document's substantive content (trích yếu, nội dung, căn cứ pháp lý) — every field is caller-supplied and mechanically validated; this only maps already-written text onto the correct NĐ 30/2020 layout/font/size, never invents wording or legal grounds.
- (vnnd30 mode) Doesn't verify that a cited legal document (e.g. inside `noi_dung_doan`) is real or in effect — that's `legal-citation-checker`'s/`legal-research-brief`'s job, not this rendering layer's.
- (vnnd30 mode) Doesn't install Typst itself — that's `typst-bootstrap`, run separately, same relationship `xelatex-bootstrap` has to the book/report scaffold mode.

## Bundled files

- `scripts/init_project.py` — the book/report scaffold script (XeLaTeX), pure stdlib.
- `references/vietnamese-latex-setup.md` — technical lessons + a sample preamble + common errors (book/report scaffold mode).
- `scripts/render_nd30_document.py` — vnnd30 mode: validates + renders a Vietnamese administrative document to `.typ` (+ optional `--compile` to PDF via Typst).
- `scripts/export_nd30_docx.py` — same validated content JSON, exported straight to DOCX via Pandoc.
- `scripts/build_reference_docx.py` — one-time build script for `assets/reference-vn-nd30.docx` (re-run only if the desired default font/size/heading-color changes).
- `assets/vnnd30.typ` — the NĐ 30/2020 formatting layer in Typst (functions mapped from the real Phụ lục I table).
- `assets/reference-vn-nd30.docx` — Pandoc `--reference-doc` template (Times New Roman, black headings — see "DOCX export" below).
- `references/nd30-2020-formatting.md` — the grounding table/citations this mode implements.
- `references/loai_van_ban_viet_tat.json` — the real Phụ lục III tên-loại abbreviation table.
- `assets/{cong_van,quyet_dinh,van_ban_ten_loai,nghi_quyet,bien_ban}_content_example.json` — real, compiling example content for each of the 5 supported `doc_kieu`.

## vnnd30 mode — render a real NĐ 30/2020 administrative document

```bash
python scripts/render_nd30_document.py <content.json> <output_dir> [--compile] [--margin-top MM] [--margin-bottom MM] [--margin-left MM] [--margin-right MM]
```

`doc_kieu` selects the layout: `"cong_van"` (Mẫu 1.5), `"quyet_dinh_truc_tiep"` (Mẫu 1.2 — also covers Mẫu 1.3's "quy định gián tiếp" variant, same layout, only the trích_yếu/Điều 1 wording differs, e.g. "Ban hành (Phê duyệt) ..."), `"van_ban_ten_loai"` (Mẫu 1.4 — the shared generic layout for chỉ thị/quy chế/quy định/thông báo/hướng dẫn/chương trình/kế hoạch/phương án/đề án/dự án/báo cáo/tờ trình), `"nghi_quyet"` (Mẫu 1.1), or `"bien_ban"` (Mẫu 1.9 — structurally different: no separate địa danh/ngày header line, a 2-column THƯ KÝ/CHỦ TỌA signature footer instead of Nơi nhận + quyền hạn-chức vụ). See the 5 bundled example content JSONs for the exact schema each `doc_kieu` needs. `--compile` runs a real `typst compile` (single pass) if Typst is found at `.tools/typst/` (shared location, see `typst-bootstrap`) or on `PATH`. `--margin-*` overrides the default margin within NĐ 30/2020's own permitted range (top/bottom 20-25mm, left 30-35mm, right 15-20mm) — a value outside the legal range is refused, not clamped. Exit 0 = rendered (and compiled if requested), 1 = validation issues (nothing written), 2 = malformed input.

Số/ký hiệu: `"<so>/<loai_vt-hoac-coquan_vt>-<donvi_vt>"`, **no year** — every doc_kieu here is a "văn bản hành chính cá biệt" (an individual administrative act), which per Phụ lục III's real mẫu images never embeds a year in số/ký hiệu. This is a DIFFERENT convention from `legal-citation-checker`'s with-year regex, which validates CITATIONS to a normative law document (e.g. "30/2020/NĐ-CP") — that convention does not apply to anything authored by this script. `ten_loai` (for `van_ban_ten_loai`) is checked against `references/loai_van_ban_viet_tat.json`'s real Phụ lục III table; an unrecognized name/abbreviation pair is refused, not guessed. A collective-body signature ("TM. ỦY BAN NHÂN DÂN" + chức vụ on its own line below, Phụ lục I Mục II.7.c) is requested via `nguoi_ky.tap_the` (requires a non-empty `quyen_han`).

Escaping: caller-supplied free text is escaped for Typst string literals (`typst_escape()`) — only `\` and `"` need it inside a quoted string, a narrower/simpler rule than LaTeX's ~9 special characters. Verified real against `&`, `%`, `#`, `_`, `*`, literal quotes, and a literal backslash — all display literally, none trigger Typst markup (bold/italic/heading) or break compilation.

## DOCX export — same content, Times New Roman/black, not Pandoc's stock template

```bash
python scripts/export_nd30_docx.py <content.json> <output.docx>
```

Validates the same content JSON `render_nd30_document.py` does, but renders it to **Markdown** (not the `.typ` — Pandoc has no Typst reader at all, and even if it did, this keeps the DOCX path engine-agnostic), then converts via `pandoc -f markdown -t docx --reference-doc=assets/reference-vn-nd30.docx`. Without a custom reference-doc, Pandoc's own default DOCX template uses "Aptos" and colors Heading1-9 in stock blue/teal accent colors (`0F4761`/`365F91`/`4F81BD`/`595959`/`272727`) — exactly the "template override / colored heading instead of black" failure mode that motivated building this. `reference-vn-nd30.docx` was built (see `build_reference_docx.py`) by patching pandoc's own default reference.docx: `word/theme/theme1.xml`'s majorFont/minorFont → Times New Roman, `word/styles.xml`'s docDefaults size 24→26 half-points (13pt, matching NĐ 30/2020's nội dung cỡ chữ), and every Heading1-9 (+ Char variant) `w:color` → `000000`. The exact same 3-step patch (not the file itself) as a real, working fix already in a sibling project, `D:/elix/praxis_csc/resources/templates/reference-vn.docx` — see that project's `docs/CHANGELOG.md` (2026-07-20 entry) for its own account of the same bug.

## Verified

Book/report scaffold: real 4-pass build (xelatex→biber→xelatex→xelatex), 5-page PDF with correctly-rendered Vietnamese diacritics.

vnnd30 mode, Typst engine (2026-07-27): `typst-bootstrap` installed Typst 0.15.1 for real (downloaded from the official GitHub release, extracted to `.tools/typst/`). All 5 example content JSONs (`cong_van`, `quyet_dinh_truc_tiep`, `van_ban_ten_loai`, `nghi_quyet`, `bien_ban`) rendered AND compiled for real via a single `typst compile` pass, PDFs visually inspected page by page — correct 2-column header (via Typst's `grid()`, not LaTeX minipages), correct Vietnamese diacritics throughout, correct font sizes/bold/italic per the Phụ lục I table, "THẨM QUYỀN BAN HÀNH" heading present, "TM. HỘI ĐỒNG NHÂN DÂN"/"CHỦ TỊCH" 2-line collective signature rendered correctly, `bien_ban`'s THƯ KÝ/CHỦ TỌA 2-column footer rendered correctly, page numbering correctly suppressed on page 1 and shown on page 2+ (via Typst's `context`/`counter(page)`, one compile pass, no LaTeX-style multi-pass requirement). `--margin-top/bottom/left/right` verified real: a valid override compiled correctly, an out-of-range value (50mm) correctly refused before writing anything. 9 deliberately broken content JSONs across all doc_kieu each refused with the exact expected reason (unchanged from the LaTeX version — `validate()` wasn't touched by the engine swap). A real Typst-special-character stress test (`&`, `%`, `#`, `_`, `*`, literal double-quotes, a literal backslash) compiled cleanly with every character displayed literally, no markup injection. **1 real bug found and fixed during the Typst port**: a literal `"- "` at the start of a markup line is parsed by Typst as a bullet-list marker (rendering `•` instead of the literal dash the real mẫu uses) — fixed in `nd-kinhgui`/`nd-noinhan` by building the line via string concatenation in code mode instead of markup mode. A separate real bug (an off-by-one in `typst-bootstrap`'s `REPO_ROOT` path computation, `parents[2]` instead of `parents[3]`) was found and fixed before Typst's install was attempted for real.

DOCX export (2026-07-27, unaffected by the engine swap): `reference-vn-nd30.docx` verified real — extracted and confirmed `word/theme/theme1.xml`'s latin typeface is "Times New Roman" (not Aptos) and every `w:color` in `word/styles.xml` is `000000` (not Pandoc's stock colors). All 5 example content JSONs exported to real `.docx` files via actual `pandoc` calls, re-opened with `python-docx` and verified: correct table structure, correct text content including all Vietnamese diacritics, and zero explicit `w:color` elements anywhere (confirmed by direct XML inspection).

## Known limitations (v0.4.0)

- Only scaffolds a simple `book` class (1 sample chapter) — doesn't yet support multi-volume, TikZ figures, or custom environments (things the source project has but which are project-specific, not immediately generalizable).
- Not tested with fonts other than "Noto Serif"/"Times New Roman" — if a font isn't on the build machine, `xelatex` reports a clear error ("Font not found"), no silent failure. (vnnd30 mode: Typst's own font-fallback behavior if Times New Roman is missing on a target machine hasn't been separately tested — this machine has it as a system font.)
- vnnd30 mode covers 5 of the ~10 real mẫu in Phụ lục III's Mục II: **not yet built** — Công điện (Mẫu 1.6), Giấy mời/Giấy giới thiệu/Giấy nghỉ phép (Mẫu 1.7-1.10) — all smaller/simpler forms than what's covered, lower priority.
- DOCX export is Markdown-mediated, not a literal rendering of the Typst layout — visually close but not pixel-identical to the PDF (e.g. exact header column widths depend on Word's own table auto-layout). Good enough for "correct content, correct font, no color override," not a guarantee of pixel-for-pixel PDF/DOCX parity.
- Page margins are validated within NĐ 30/2020's permitted range but the font-size choices inside `vnnd30.typ` (e.g. Quốc hiệu fixed at 12pt, not the alternative 13pt) are still fixed, not yet exposed as configurable options.
- `typst-bootstrap`'s install has only been verified for real on Windows x86_64 — the macOS/Linux asset download paths are written by analogy, not independently tested (see that skill's own Known limitations).
- Only verified by rendering/compiling/exporting the 5 bundled synthetic examples on this machine — not yet exercised against a real government document a real agency actually issued, and not yet cross-checked against a real printed NĐ 30/2020 document side-by-side for pixel-level layout fidelity (the sơ đồ in Phụ lục I is a general position guide, not a pixel grid).
