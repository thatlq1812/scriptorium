---
name: python-env-bootstrap
description: Create/extend ONE shared Python venv at the repo root (sibling to `skills/`), even on a machine that does NOT have Python installed — uses uv (Astral), a static binary that downloads a standard Python itself. Use when another skill declares a `requirements.txt` and needs to be installed into the shared runtime environment. Do NOT use to permanently install Python system-wide or to replace the user's package manager — this only manages the repo's shared venv.
license: MIT
compatibility: Requires downloading/installing `uv` (the official astral.sh install script, no pre-existing Python needed). Verified running clean: Claude Code, Windows via real PowerShell (2026-07-26). See "Verified" section below for real test-case detail.
metadata:
  domain: meta
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (docs/archive/pre-spec-2026-07-26/note.md point 3): the idea of a skill 'containing a full python version inside it' so ordinary users can run a skill needing complex Python without installing anything first. Updated 2026-07-26: owner requested moving from venv-per-skill to a shared venv at the root — avoids duplicating heavy dependencies (torch...) across skills."
  version: 0.2.0
---

# python-env-bootstrap

A shared infrastructure skill: bootstraps/extends ONE shared Python venv at the repo root (`<repo_root>/.venv`, sibling to `skills/`) for other skills that need Python, based on `uv` — a ~15MB static binary that downloads a portable Python itself, no pre-installed Python required.

## Why a shared venv, not one venv per skill

**Direction change 2026-07-26 (owner)**: previously each skill had its own `.venv` inside the skill folder — leading to duplicated heavy dependencies (e.g. `torch` ~2GB, reinstalled repeatedly across skills sharing the same ML stack). A shared venv at the root solves this: install once, every Python skill shares it. Verified for real: `document-ai-structurer` + `office-doc-creator` + `image-generator-gemini` all installed into the same venv, no cross-import conflicts (`docling`, `python-docx/pptx`, `openpyxl`, `google-genai` all coexist cleanly).

## Why not use Python's standard `venv`

`python -m venv` requires Python already installed on the machine — doesn't match the owner's "ordinary user" assumption. `uv` fills exactly this gap: install `uv` (no Python needed) → `uv python install` downloads a standard Python → `uv venv` + `uv pip install` as usual.

## Principle — never commit a venv (repeated from `docs/specs/STRATEGY_SPEC.md` §7.7)

This skill does NOT create or commit any venv into git. It's purely bootstrap logic that runs when needed — the venv is always created fresh on the running machine, and sits in `.gitignore` at the repo root.

## Using it for another skill

The target skill must have a `requirements.txt` at its root. Run (from the repo root):

```bash
# Real Unix/macOS (do NOT run via Git Bash/MSYS2 on Windows — see the warning below):
bash skills/python-env-bootstrap/scripts/bootstrap.sh skills/<target_skill>/requirements.txt [python_version]

# Windows: ALWAYS run via real PowerShell, not Git Bash:
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\<target_skill>\requirements.txt [-PyVersion 3.12]
```

Result: `<repo_root>/.venv` is ready (created if missing, extended if it already exists), with the right Python version + the calling skill's dependencies added — this venv is shared by EVERY Python skill in the repo, no new venv is created per call.

## Warning confirmed by a real bug: don't run `bootstrap.sh` from Git Bash/MSYS2 on Windows

Running `bootstrap.sh` inside Git Bash (MINGW64/MSYS2) on Windows causes `uv` to **misdetect the platform as `linux-x86_64-gnu`** (because MSYS2's `uname` returns a Linux-like value) and download an unusable Linux Python build — the resulting venv has a symlink pointing to a path that doesn't exist (`/home/<user>/.local/share/uv/python/...`), producing a "No such file" error when invoked. On Windows, `bootstrap.ps1` must run through real PowerShell (not Git Bash calling powershell.exe nested inside it) so `uv` correctly detects `x86_64-pc-windows-msvc`. Reproduced and fixed for real on 2026-07-26 while bootstrapping `document-ai-structurer`.

## Verified

The shared root venv successfully installed dependencies for 3 skills (document-ai-structurer, office-doc-creator, image-generator-gemini), no cross-import conflicts. Running via Git Bash/MSYS2 on the same Windows machine fails — see the warning in the body. Not yet verified: real macOS/Linux, OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI.

## Known limitations (v0.2.0)

- A shared venv means EVERY Python skill uses the same dependency versions — if 2 skills need different versions of the same package, that's a real conflict (hasn't happened yet, but needs watching as new Python skills are added).
- Verified working correctly on Windows via real PowerShell. The `.sh` script is written to POSIX standards but hasn't been tested for real on macOS/Linux.
- Installing `uv` for the first time needs network access (downloading the installer from astral.sh) — not fully offline-capable on the first run.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit).

## Skills depending on this skill

- `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini` (see `registry/skills.json`, `dependencies` field).
