---
name: xelatex-bootstrap
description: 'SUPERSEDED 2026-08-13 by toolchain-bootstrap -- do not use for new work, content unchanged and kept for reference. Detects whether the XeLaTeX toolchain (xelatex, biber, the fontspec LaTeX package) is present on this machine, and only when explicitly run, installs it via the platform''s package manager (winget/brew/apt). Use before latex-project-bootstrap on a machine where the toolchain hasn''t already been confirmed present — latex-project-bootstrap assumes xelatex/biber already exist and doesn''t install them itself. Do NOT run the install script speculatively — always run check_toolchain.py first; installing is a multi-minute, several-hundred-MB system change and should only happen when detection actually shows something missing.'
license: MIT
compatibility: 'check_toolchain.py is stdlib-only (shutil, subprocess, platform), no dependency, no venv. install_toolchain.ps1 requires winget (Windows); install_toolchain.sh requires brew (macOS) or apt-get (Debian/Ubuntu Linux). Verified running clean: Claude Code, Windows (2026-07-27). See "Verified" section below for real test-case detail.'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-27, via another agent's request.md proposal, reviewed and partially accepted): latex-project-bootstrap already scaffolds XeLaTeX projects correctly but assumes the toolchain is already installed (its own compatibility line says so) -- this is the missing 'install the toolchain itself' layer, same relationship python-env-bootstrap has to every Python skill (uv downloads a portable Python; this downloads/installs MiKTeX/TeX Live/MacTeX). Split into detect (safe, default) vs install (heavy, explicit-only) following python-env-bootstrap's own established pattern of never silently taking a heavy system action."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# xelatex-bootstrap

Detects the XeLaTeX toolchain (xelatex + biber + fontspec) and, only when explicitly asked, installs it. Mirrors `python-env-bootstrap`'s relationship to Python skills: `latex-project-bootstrap` scaffolds a project assuming the toolchain exists; this skill is what actually gets it there on a machine that doesn't have it yet.

## Detect (safe, always run first)

```bash
python skills/general/xelatex-bootstrap/scripts/check_toolchain.py
```

Read-only — checks `xelatex --version`, `biber --version`, and `kpsewhich fontspec.sty`, reports each as OK/MISSING with the real version string when found. Exit 0 = everything present, `latex-project-bootstrap` can build. Exit 1 = something missing, prints the install command for the detected platform (Windows/macOS/Linux) and does NOT install anything itself.

## Install (heavy — only run after detect shows something missing)

```bash
# Windows (real PowerShell, not Git Bash -- same platform-detection caveat python-env-bootstrap documents):
.\skills\general\xelatex-bootstrap\scripts\install_toolchain.ps1
# macOS/Linux:
bash skills/general/xelatex-bootstrap/scripts/install_toolchain.sh
```

Windows installs MiKTeX via `winget`; macOS installs MacTeX (no-GUI) via `brew`; Linux (Debian/Ubuntu) installs `texlive-xetex` + `texlive-lang-vietnamese` + `biber` via `apt-get` (needs `sudo`). MiKTeX installs missing LaTeX packages (fontspec, polyglossia...) on the fly on first compile by default, so no separate package-install step is needed after it's installed. This is a multi-minute, several-hundred-MB-to-multi-GB operation — never run it without first confirming via `check_toolchain.py` that something is actually missing.

## What this skill does NOT do

- Doesn't scaffold a LaTeX project — that's `latex-project-bootstrap`, which depends on this skill's job being done first (or the toolchain already being present).
- Doesn't install anything on its own initiative — `check_toolchain.py` never calls the install scripts; a human/agent decides to run `install_toolchain.ps1`/`.sh` after seeing MISSING output.
- Doesn't manage a shared venv — unrelated to `python-env-bootstrap`; this is a system-level LaTeX toolchain, not a Python environment.

## Verified

check_toolchain.py correctly detected an already-installed MiKTeX 25.12 (xelatex, biber, fontspec.sty all found with real version strings), and correctly reports a missing binary when tested directly against a nonexistent binary name. install_toolchain.ps1/.sh NOT executed for real this session (heavy system-modifying operation, no machine available without an existing toolchain to test against) — written carefully but flagged as unverified in Known limitations.

## Known limitations (v0.1.0, not yet through official quality-eval)

- `install_toolchain.ps1`/`.sh` were NOT executed for real this session — the only available test machine already has MiKTeX 25.12 installed, so there was nothing to install against. Written by direct analogy to real, documented install commands (winget MiKTeX package id, apt texlive-xetex, brew mactex-no-gui) but not run end-to-end. Flag this to whoever runs it on a genuinely toolchain-less machine first.
- No Linux package manager other than `apt-get` is handled (no `dnf`/`pacman`/`zypper` branch) — refuses cleanly with a manual-install message on those distros rather than guessing a wrong command.
- `check_fontspec()` depends on `kpsewhich` being on PATH, which itself ships with the TeX distro — on a machine with truly nothing installed, this check correctly reports MISSING (kpsewhich itself absent) rather than crashing.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit).

## Skills depending on this skill

- `latex-project-bootstrap` (should be run before it on an unconfirmed machine, not yet declared as a formal `dependencies` entry in `registry/skills.json` since it's optional — the toolchain may already exist).
