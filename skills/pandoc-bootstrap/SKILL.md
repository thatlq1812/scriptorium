---
name: pandoc-bootstrap
description: Detects whether `pandoc` is present on this machine, and only when explicitly run, installs it via the platform's package manager (winget/brew/apt). Use before any skill needs to convert between .tex/.docx/.pdf/.html and hasn't confirmed pandoc is already installed. Converting TO .pdf additionally needs a working LaTeX engine (see xelatex-bootstrap) — this skill only manages pandoc itself. Do NOT run the install script speculatively — always run check_pandoc.py first.
license: MIT
compatibility: check_pandoc.py is stdlib-only (shutil, subprocess, platform), no dependency, no venv. install_pandoc.ps1 requires winget (Windows); install_pandoc.sh requires brew (macOS) or apt-get (Debian/Ubuntu Linux). Verified running clean: Claude Code, Windows (2026-07-27) — check_pandoc.py correctly detected an already-installed pandoc 3.8.1 (real version string), and correctly reports missing when pandoc is unavailable (verified by simulating a missing binary). install_pandoc.ps1/.sh NOT executed for real this session (no machine available without pandoc already installed) — flagged as unverified in Known limitations.
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-27, via another agent's request.md proposal, reviewed and accepted): a document-format-conversion bootstrap skill, complementing xelatex-bootstrap and distinct from office-doc-creator (which uses python-docx/pptx/openpyxl directly, not pandoc) -- same detect-first/install-only-when-explicit pattern as python-env-bootstrap and xelatex-bootstrap."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# pandoc-bootstrap

Detects `pandoc` and, only when explicitly asked, installs it. Same detect-first/install-only-when-explicit shape as `xelatex-bootstrap`/`python-env-bootstrap`.

## Detect (safe, always run first)

```bash
python skills/pandoc-bootstrap/scripts/check_pandoc.py
```

Read-only — checks `pandoc --version`, reports OK/MISSING with the real version string when found. Exit 0 = present. Exit 1 = missing, prints the install command for the detected platform, installs nothing itself.

## Install (only run after detect shows it's missing)

```bash
# Windows (real PowerShell, not Git Bash):
.\skills\pandoc-bootstrap\scripts\install_pandoc.ps1
# macOS/Linux:
bash skills/pandoc-bootstrap/scripts/install_pandoc.sh
```

Windows via `winget`, macOS via `brew`, Linux (Debian/Ubuntu) via `apt-get` (needs `sudo`).

## What this skill does NOT do

- Doesn't install a LaTeX engine — converting TO `.pdf` needs one; see `xelatex-bootstrap`. This skill only manages `pandoc` itself, so it stays useful for .tex/.docx/.html conversions even on a machine that never needs PDF output.
- Doesn't duplicate `office-doc-creator` — that skill builds `.docx`/`.xlsx`/`.pptx` directly via `python-docx`/`openpyxl`/`python-pptx`, no `pandoc` involved. This skill is for format *conversion* (e.g. `.tex` → `.docx`), not building an Office file from scratch.
- Doesn't install anything on its own initiative — `check_pandoc.py` never calls the install scripts.

## Known limitations (v0.1.0, not yet through official quality-eval)

- `install_pandoc.ps1`/`.sh` were NOT executed for real this session — the only available test machine already has pandoc installed. Written by direct analogy to real, documented install commands (winget package id, apt/brew package name) but not run end-to-end.
- No Linux package manager other than `apt-get` is handled — refuses cleanly with a manual-install message on other distros.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit).
