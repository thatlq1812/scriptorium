---
name: toolchain-bootstrap
description: Detects or installs the 5 toolchains other Scriptorium skills depend on — the shared Python venv (via `uv`, for any skill declaring `requirements.txt`), ffmpeg (portable, bundled inside the `imageio-ffmpeg` pip wheel), pandoc, the Typst binary, and the XeLaTeX toolchain (xelatex + biber + fontspec). Use whenever a skill needs one of these five bootstrapped before it can run, or when a script fails because python/ffmpeg/pandoc/typst/xelatex isn't found. Always detect first (each tool's `check_*.py`, safe/read-only) — only install when detection actually shows something missing; installing is a real system/network action, never run speculatively. Do NOT use this to run any of the tools themselves — it only gets them present on the machine; rendering/compiling/converting/transcoding is each dependent skill's own job.
license: MIT
compatibility: 'Network access needed on first install of any component. Python venv via `uv` (astral.sh). ffmpeg bundled inside the `imageio-ffmpeg` pip wheel (no separate download). pandoc/xelatex via platform package manager (winget/brew/apt). Typst downloads a static binary from github.com/typst/typst releases (no package manager). Verified running clean: Claude Code, Windows — see "Verified" section below.'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-13): merge of 5 previously-separate bootstrap skills (python-env-bootstrap, ffmpeg-bootstrap, pandoc-bootstrap, typst-bootstrap, xelatex-bootstrap) into one skill_id, following thatlq1812's own architecture review of a Gemini-authored restructuring proposal (STRATEGY_01.md) — approved specifically because all 5 already shared the exact same detect-first/install-only-when-explicit shape and each one's own elicited_from already cited the others as its architectural precedent, unlike the proposal's broader 74-to-14 merge (rejected — see the same review for why). latex-project-bootstrap and browser-web-renderer were deliberately NOT folded in despite being tagged 'bootstrap' in the original proposal: the former is project scaffolding that assumes a toolchain already installed (a consumer of this skill, not an instance of it), the latter ingests uncontrolled external web content (stage4_required: true, risk_tier N2) — a materially different risk class from a pure local-toolchain installer. Content/scripts carried forward verbatim from the 5 source skills, only paths/filenames updated for the new location; no detection/install logic was rewritten. domain reclassified meta -> general for the merged skill_id (matching 3 of the 5 originals and SCHEMA.md's own definition — 'general' for pure task-type skills useful across every domain — python-env-bootstrap's prior 'meta' tag and ffmpeg-bootstrap's 'media' tag were both narrower than their actual cross-domain usage)."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# toolchain-bootstrap

Detects or installs 5 toolchains other skills in this registry depend on. Each one keeps the same detect-first/install-only-when-explicit shape: a `check_*` script is always safe to run (read-only, zero side effects) and tells you exactly what's missing and the exact install command; the matching `install_*` script only runs when you decide to, after seeing something is actually missing.

## Routing — which tool do you need?

| Need | Detect (always safe) | Install (only after detect shows MISSING) |
|---|---|---|
| Python venv for a skill's `requirements.txt` | *(bootstrap.ps1/.sh does detect+install in one step — see below)* | `scripts/bootstrap.ps1` / `scripts/bootstrap.sh` |
| `ffmpeg` | `scripts/check_ffmpeg.py` | `uv pip install` (primary) or `scripts/install_ffmpeg_system.ps1`/`.sh` (optional, system-wide) |
| `pandoc` | `scripts/check_pandoc.py` | `scripts/install_pandoc.ps1` / `.sh` |
| Typst binary | `scripts/check_typst.py` | `scripts/install_typst.py` |
| XeLaTeX toolchain (xelatex + biber + fontspec) | `scripts/check_xelatex.py` | `scripts/install_xelatex.ps1` / `.sh` |

---

## 1. Python venv (`bootstrap.ps1` / `bootstrap.sh`)

Creates/extends ONE shared Python venv at the repo root (`<repo_root>/.venv`, sibling to `skills/`), even on a machine that does NOT have Python installed — uses `uv` (Astral), a static binary that downloads a standard Python itself.

The target skill must have a `requirements.txt` at its root:

```bash
# Real Unix/macOS shell (do NOT run via Git Bash/MSYS2 on Windows — see the warning below):
bash skills/general/toolchain-bootstrap/scripts/bootstrap.sh skills/<target_skill>/requirements.txt [python_version]

# Windows: ALWAYS run via real PowerShell, not Git Bash:
.\skills\general\toolchain-bootstrap\scripts\bootstrap.ps1 -Requirements skills\<target_skill>\requirements.txt [-PyVersion 3.12]
```

Result: `<repo_root>/.venv` is ready (created if missing, extended if it already exists), shared by EVERY Python skill in the repo — no new venv is created per call. Never commit this venv into git (`.gitignore`).

### Why a shared venv, not one per skill

Avoids duplicating heavy dependencies (e.g. `torch`) across skills that need the same ML stack. Verified for real: `document-ai-structurer` + `office-doc-creator` + `gemini-generator` all installed into the same venv, no cross-import conflicts.

### Why not Python's standard `venv`

`python -m venv` requires Python already installed — doesn't match the "ordinary user, nothing pre-installed" assumption. `uv` fills this gap: install `uv` (no Python needed) → `uv python install` downloads a standard Python → `uv venv` + `uv pip install` as usual.

### Warning confirmed by a real bug: don't run `bootstrap.sh` from Git Bash/MSYS2 on Windows

Running `bootstrap.sh` inside Git Bash (MINGW64/MSYS2) on Windows causes `uv` to **misdetect the platform as `linux-x86_64-gnu`** (MSYS2's `uname` returns a Linux-like value) and download an unusable Linux Python build. On Windows, `bootstrap.ps1` must run through real PowerShell so `uv` correctly detects `x86_64-pc-windows-msvc`. Reproduced and fixed for real 2026-07-26.

---

## 2. ffmpeg (`check_ffmpeg.py` / `resolve_ffmpeg.py` / `install_ffmpeg_system.*`)

Resolves a working `ffmpeg` binary for other skills to call via `subprocess` — PORTABLE-first: `imageio-ffmpeg`'s pip wheel bundles the actual ffmpeg executable inside itself, so installing it into the shared venv is the entire "install," no separate download, no dependency on the host's PATH.

```bash
# Bootstrap (normal path — same one-liner as any other skill's requirements.txt):
uv pip install --python .venv -r skills/general/toolchain-bootstrap/requirements.txt

# Detect (safe, always run to confirm, zero network):
.venv\Scripts\python.exe skills\general\toolchain-bootstrap\scripts\check_ffmpeg.py
```

From another skill's script:

```python
from resolve_ffmpeg import resolve_ffmpeg_path  # path-import from this skill's scripts/

ffmpeg_path = resolve_ffmpeg_path()  # local/portable first, system PATH as last-resort fallback
```

`resolve_ffmpeg_path()` resolution order: (1) `imageio_ffmpeg`'s bundled binary — project-local, portable, recommended; (2) `ffmpeg` on system PATH, only if `imageio-ffmpeg` isn't installed. Raises `RuntimeError` naming the exact bootstrap command if neither resolves — never triggers a network call itself.

`install_ffmpeg_system.ps1`/`.sh` are OPTIONAL, secondary — a real system-wide install (winget/brew/apt/dnf/pacman), only useful if ffmpeg is also wanted outside this project. `resolve_ffmpeg_path()` never depends on this being run.

### What this skill does NOT do (ffmpeg)

Does not transcode, edit, cut, or compose any media itself — pure path-resolution. See `video-assembly-composer` for actual ffmpeg-driven rendering.

---

## 3. pandoc (`check_pandoc.py` / `install_pandoc.*`)

Detects `pandoc` and, only when explicitly asked, installs it via the platform's package manager.

```bash
python skills/general/toolchain-bootstrap/scripts/check_pandoc.py   # detect, read-only, exit 0 = present

# Windows (real PowerShell, not Git Bash):
.\skills\general\toolchain-bootstrap\scripts\install_pandoc.ps1
# macOS/Linux:
bash skills/general/toolchain-bootstrap/scripts/install_pandoc.sh
```

Windows via `winget`, macOS via `brew`, Linux (Debian/Ubuntu) via `apt-get` (needs `sudo`).

### What this skill does NOT do (pandoc)

Doesn't install a LaTeX engine — converting TO `.pdf` needs one; see the XeLaTeX section below. Doesn't duplicate `office-doc-creator` (that builds `.docx`/`.xlsx`/`.pptx` directly via `python-docx`/`openpyxl`/`python-pptx`, no pandoc). This is for format *conversion* (e.g. `.tex` → `.docx`).

---

## 4. Typst binary (`check_typst.py` / `install_typst.py`)

Detects whether the Typst typesetting binary is available (checked at the shared repo-local `.tools/typst/` location first, then PATH), and only when explicitly run, downloads the official static binary from `github.com/typst/typst` releases into that shared location — no system package manager, no multi-GB TeX distribution, ~50MB total.

```bash
python skills/general/toolchain-bootstrap/scripts/check_typst.py     # detect, read-only
python skills/general/toolchain-bootstrap/scripts/install_typst.py   # only after detect shows MISSING
```

Idempotent — `install_typst.py` does nothing and exits 0 if the binary is already there. Doesn't touch system PATH or install anything system-wide — lives entirely inside `.tools/typst/` (gitignored, like `.venv/`), invoked by absolute path by whichever skill needs it (`latex-project-bootstrap`'s vnnd30 mode).

---

## 5. XeLaTeX toolchain (`check_xelatex.py` / `install_xelatex.*`)

Detects whether the XeLaTeX toolchain (xelatex, biber, the fontspec LaTeX package) is present, and only when explicitly run, installs it via the platform's package manager. This is a multi-minute, several-hundred-MB-to-multi-GB system change — never run install without first confirming via `check_xelatex.py` that something is actually missing.

```bash
python skills/general/toolchain-bootstrap/scripts/check_xelatex.py   # detect, read-only

# Windows (real PowerShell, not Git Bash):
.\skills\general\toolchain-bootstrap\scripts\install_xelatex.ps1
# macOS/Linux:
bash skills/general/toolchain-bootstrap/scripts/install_xelatex.sh
```

Windows installs MiKTeX via `winget`; macOS installs MacTeX (no-GUI) via `brew`; Linux (Debian/Ubuntu) installs `texlive-xetex` + `texlive-lang-vietnamese` + `biber` via `apt-get`. MiKTeX installs missing LaTeX packages (fontspec, polyglossia...) on the fly on first compile, so no separate package-install step is needed after.

### What this skill does NOT do (XeLaTeX)

Doesn't scaffold a LaTeX project — that's `latex-project-bootstrap`, which depends on this skill's job being done first (or the toolchain already being present). This is a system-level LaTeX toolchain, unrelated to the Python venv managed by §1.

---

## Bundled files

```
skills/general/toolchain-bootstrap/
├── requirements.txt          # imageio-ffmpeg==0.6.0 (ffmpeg's own bootstrap dependency)
└── scripts/
    ├── bootstrap.ps1 / .sh                          # §1 python venv
    ├── check_ffmpeg.py, resolve_ffmpeg.py,           # §2 ffmpeg
    │   install_ffmpeg_system.ps1 / .sh
    ├── check_pandoc.py, install_pandoc.ps1 / .sh     # §3 pandoc
    ├── check_typst.py, install_typst.py              # §4 typst
    └── check_xelatex.py, install_xelatex.ps1 / .sh   # §5 xelatex
```

## Verified

Each sub-tool's detect/install logic is carried forward unchanged from its original skill (only paths/filenames updated for the merged location) — see each section above for the real test evidence already recorded before the merge: python venv (2026-07-26, 3 real skills installed with no conflicts), ffmpeg (2026-08-05, real 88MB binary confirmed installed via the wheel), typst (2026-07-27, real end-to-end download+install+idempotent-rerun), pandoc and xelatex detect paths (2026-07-27, real already-installed versions correctly detected; their install scripts were not exercised end-to-end in the original sessions either, since no toolchain-less test machine was available — carried forward as a known limitation, not newly introduced by this merge).

Post-merge re-verification (2026-08-13): `check_ffmpeg.py`, `check_pandoc.py`, `check_typst.py`, `check_xelatex.py` all re-run from the new `skills/general/toolchain-bootstrap/scripts/` location and confirmed to still correctly detect the already-installed real toolchains on this machine, with correct new paths in their own printed hints.

## Known limitations

- Same per-tool limitations as before the merge (see each section) — this merge changed file locations and cross-references only, not detection/install logic.
- A shared venv means EVERY Python skill uses the same dependency versions — if 2 skills need different versions of the same package, that's a real conflict (hasn't happened yet).
- `install_pandoc`/`install_xelatex`'s install scripts remain unexercised end-to-end (no toolchain-less test machine available) — flag this to whoever runs one on a genuinely clean machine first.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) — not required for this tier, see `registry/SCHEMA.md`.

## Skills depending on this skill

- Python venv: `document-ai-structurer`, `office-doc-creator`, `gemini-generator`, `slide-deck-composer`, `browser-web-renderer` (see `registry/skills.json` `dependencies` field).
- ffmpeg: `gemini-generator`, `video-assembly-composer`, `media-pipeline-orchestrator`.
- Typst: `latex-project-bootstrap` (vnnd30 mode only — the book/report scaffold mode uses the XeLaTeX toolchain instead, from this same skill).
