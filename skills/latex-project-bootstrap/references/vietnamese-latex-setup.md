# LaTeX + Vietnamese — set it up correctly from the start

A lesson drawn from a real LaTeX project (the `D:/elix/researches/textbooks` textbook program, in real production use, not theory): **always use XeLaTeX, never pdfLaTeX + the `vietnamese` babel package** for serious Vietnamese documents.

## Why XeLaTeX

- **pdfLaTeX + `babel[vietnamese]`**: uses old 8-bit font encoding, prone to tone-mark/diacritic bugs when combined with modern fonts, limits font choice to those with full Vietnamese Unicode support.
- **XeLaTeX + `fontspec` + `polyglossia`**: handles Unicode directly (native UTF-8), works with any TrueType/OpenType font installed on the system (Times New Roman, Noto Sans, Google Fonts...) as long as the font has Vietnamese glyphs — no specialized LaTeX font needed.

## Minimal correct preamble

```latex
\documentclass[11pt]{book}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{vietnamese}
\setmainfont{Noto Serif}       % or any Unicode font available on the machine
\setsansfont{Noto Sans}
```

Compile with `xelatex`, NOT `pdflatex` — the two engines are incompatible with `fontspec`.

## Bibliography — use biber, not bibtex

`biblatex` + `biber` handle Unicode better than classic `bibtex` (which is 8-bit-limited like pdfLaTeX). The standard build order for a document with a bibliography:

```
xelatex main.tex   # pass 1: generates .aux, .bcf
biber main          # reads .bcf, generates .bbl from bibliography.bib
xelatex main.tex   # pass 2: embeds citations
xelatex main.tex   # pass 3: finalizes cross-references (table of contents, page numbers, \ref)
```

4 commands, not 1 — skipping any pass can produce a file missing citations or with the wrong table of contents/page numbers.

## Common errors

- Forgetting to switch `pdflatex` to `xelatex` when copying an old template → `fontspec requires xetex or luatex` error.
- The font chosen in `\setmainfont` isn't on the build machine → "Font not found" error, needs installing the font or switching to another already-installed font name (`fc-list` on Linux/Mac, or check Fonts in Windows Settings).
- Using `\usepackage[utf8]{inputenc}` (not needed with XeLaTeX, the engine is already UTF-8 native — adding it doesn't error but is redundant, a sign of accidentally copying a pdfLaTeX template).
