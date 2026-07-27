---
name: typst-bootstrap
description: Detects whether the Typst typesetting binary is available (checked at the shared repo-local `.tools/typst/` location first, then PATH), and only when explicitly run, downloads the official static binary from github.com/typst/typst releases into that shared location — no system package manager, no multi-GB TeX distribution, ~50MB total. Use before latex-project-bootstrap's vnnd30 mode on a machine where Typst hasn't already been confirmed present. Do NOT run the install script speculatively — always run check_typst.py first.
license: MIT
compatibility: check_typst.py and install_typst.py are both stdlib-only (shutil/subprocess/platform/urllib/zipfile/tarfile), no dependency, no venv. Verified running clean: Claude Code, Windows (2026-07-27) — real end-to-end install (downloaded typst 0.15.1 from the official GitHub release, extracted, verified via `typst --version`), plus a real idempotent re-run (already-present short-circuit).
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-27): after comparing D:/elix/praxis_csc's real, working document-export pipeline, agreed the vnnd30 administrative-document mode in latex-project-bootstrap should move off XeLaTeX/MiKTeX (~5GB, not truly portable) onto Typst (a single ~50MB static binary, no install) for the exact portability reason praxis_csc's own docs/CHANGELOG.md records for making the same switch. This skill is the 'get Typst onto this machine' layer, same relationship python-env-bootstrap has to Python skills and xelatex-bootstrap has to the book-scaffold mode -- except here 'install' means download-and-place-a-binary, not invoke a system package manager, since that's the whole point of choosing Typst."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# typst-bootstrap

Detects the Typst binary and, only when explicitly asked, downloads it. Unlike `xelatex-bootstrap` (which invokes `winget`/`brew`/`apt-get` to install a multi-GB TeX distribution), this only downloads one ~50MB static binary from Typst's official GitHub releases into a shared repo-local location — no system package manager, no admin rights, no PATH modification needed system-wide.

## Detect (safe, always run first)

```bash
python skills/typst-bootstrap/scripts/check_typst.py
```

Read-only — checks `<repo_root>/.tools/typst/typst(.exe)` first (the shared location every Typst-dependent skill reuses, gitignored, mirrors `python-env-bootstrap`'s shared `.venv/` pattern), then falls back to PATH. Exit 0 = found, prints the real version string. Exit 1 = missing, prints the install command and does NOT install anything itself.

## Install (only run after detect shows something missing)

```bash
python skills/typst-bootstrap/scripts/install_typst.py
```

Downloads the platform-appropriate official release asset (Windows/macOS/Linux, x86_64/arm64) from `github.com/typst/typst/releases/latest`, extracts the `typst`/`typst.exe` binary, and places it at `<repo_root>/.tools/typst/`. Idempotent — does nothing and exits 0 if the binary is already there. Requires internet access; no other dependency.

## What this skill does NOT do

- Doesn't render or compile anything itself — that's `latex-project-bootstrap`'s vnnd30 mode, which depends on this skill's job being done first (or Typst already being present).
- Doesn't touch system PATH or install anything system-wide — the binary lives entirely inside this repo's `.tools/typst/` (gitignored, like `.venv/`), invoked by absolute path by whichever skill needs it.
- Doesn't manage LaTeX/XeLaTeX at all — unrelated to `xelatex-bootstrap`, which remains the correct dependency for `latex-project-bootstrap`'s *book/report scaffold* mode (that mode stays on XeLaTeX deliberately, see that skill's SKILL.md "Engine per mode").

## Verified

Real end-to-end install on this machine (2026-07-27): `check_typst.py` correctly reported MISSING before install; `install_typst.py` downloaded `typst-x86_64-pc-windows-msvc.zip` from the real GitHub release URL, extracted `typst.exe` into `.tools/typst/`, confirmed via `typst --version` → `typst 0.15.1 (9dfd3a08)`. Re-running `install_typst.py` a second time correctly short-circuited ("already present, nothing to do") instead of re-downloading. A real path-computation bug (`parents[2]` instead of `parents[3]`, resolving one directory too shallow) was found and fixed during this same testing before the install was attempted.

## Known limitations (v0.1.0, not yet through official quality-eval)

- Only the Windows x86_64 path (`typst-x86_64-pc-windows-msvc.zip`) has been verified for real. The macOS (`x86_64`/`arm64`) and Linux (`x86_64`/`aarch64`) asset-name entries in `install_typst.py`'s `PLATFORM_ASSETS` map are written by direct analogy to the same release's published asset naming convention, not independently tested on those platforms.
- No checksum/signature verification of the downloaded archive beyond HTTPS transport security — relies on GitHub's official release URL being the real source (same trust level `scout-harvester` already established for this exact repo when evaluating it as a dependency for `praxis_csc`).
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit).

## Skills depending on this skill

- `latex-project-bootstrap` (vnnd30 mode only — the book/report scaffold mode depends on `xelatex-bootstrap` instead).
