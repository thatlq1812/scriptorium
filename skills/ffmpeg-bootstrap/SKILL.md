---
name: ffmpeg-bootstrap
description: 'Resolves a working `ffmpeg` binary for other skills to call via subprocess — PORTABLE-first: the binary lives inside this project''s shared venv (`imageio-ffmpeg` bundles the real ffmpeg executable inside its pip wheel, no separate download, no system-wide install, no dependency on the host''s PATH), with system PATH ffmpeg only as a last-resort fallback. `check_ffmpeg.py` detects (safe, zero network). `resolve_ffmpeg.py` is the importable helper every media skill here (`video-generator-gemini`, `audio-generator-gemini`, `video-assembly-composer`) calls to get the resolved path — never hardcodes `"ffmpeg"` and hopes it''s on PATH. `install_ffmpeg_system.ps1`/`.sh` are OPTIONAL scripts for a real system-wide install (winget/brew/apt). Use before any skill here shells out to ffmpeg. Do NOT use this to transcode/edit/compose video or audio — it only resolves and verifies the binary path.'
license: MIT
compatibility: 'Requires Python 3.11+ and the `imageio-ffmpeg` package (via `python-env-bootstrap`''s shared venv) — the pip wheel itself contains the platform-specific ffmpeg binary (~88MB on Windows), no post-install download step. Verified running clean: Claude Code, Windows (2026-08-05) — see "Verified" below.'
metadata:
  domain: media
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Reuses the bootstrap-skill architecture already proven in this project by python-env-bootstrap (shared venv, uv-based, portable rather than relying on system state). Owner-directed correction (2026-08-05): an initial draft of this skill defaulted to system-PATH-first detection with OS-package-manager install (winget/brew/apt) as the primary path, mirroring browser-web-renderer's two-step pattern — owner flagged this as wrong for this class of tool ('tương tự như các bootstrap khác, ta cần đảm bảo nó tải về và nằm luôn trong resource... nằm local trong workspace thay vì nằm trong hệ thống... đấy mới gọi là portable'). Verified for real during that correction: `imageio-ffmpeg`'s installed wheel already contains the actual ffmpeg binary at `.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe` (~88MB) immediately after `uv pip install`, no lazy/runtime download at all in the installed version — simpler and more portable than the original design assumed. Redesigned around this finding: local-first resolution, system PATH demoted to a last-resort fallback, and the OS-package-manager scripts reframed as optional/secondary rather than the primary install path."
  version: 0.2.0
  grounding: not_applicable
  object_type: []
---

# ffmpeg-bootstrap

Resolves an ffmpeg binary other skills can call via `subprocess` — portable by construction: `imageio-ffmpeg`'s pip wheel ships the actual platform-specific ffmpeg executable inside itself, so installing it into this project's shared venv (the same `uv pip install --python .venv -r <requirements.txt>` step every other Python skill here already uses) is the entire "install," with no separate download stage and no dependency on the host machine's own PATH.

## Bootstrap (the normal path — same one-liner as any other skill's requirements.txt)

```bash
uv pip install --python .venv -r skills/ffmpeg-bootstrap/requirements.txt
```

That's it — `imageio-ffmpeg`'s wheel already contains the binary. No `install_ffmpeg.py`, no explicit heavy-download confirmation step needed (unlike `browser-web-renderer`'s Chromium, which really is a separate ~300MB download after the pip package).

## Detect (safe, always run to confirm, zero network)

```bash
.venv\Scripts\python.exe skills\ffmpeg-bootstrap\scripts\check_ffmpeg.py
```

Checks the local/portable resource first (`imageio_ffmpeg.get_ffmpeg_exe()` — instant, reads a file already on disk, never triggers a network call). Falls back to reporting a system PATH `ffmpeg` as secondary/informational only. Exit 0 if either resolves; exit 1 only if neither does.

## Using it from another skill's script

```python
from resolve_ffmpeg import resolve_ffmpeg_path  # copy or path-import from this skill's scripts/

ffmpeg_path = resolve_ffmpeg_path()  # local/portable first, system PATH as last-resort fallback
```

`resolve_ffmpeg_path()` resolution order: (1) `imageio_ffmpeg`'s bundled binary — the project-local, portable, recommended path; (2) `ffmpeg` on system PATH, only if `imageio-ffmpeg` isn't installed in the current venv for some reason. Raises `RuntimeError` naming the exact bootstrap command if neither resolves. Never triggers a network call itself — resolution is either instant (local file already on disk) or a `shutil.which` PATH lookup.

## Optional, secondary: real system-wide install

```bash
# Windows (real PowerShell):
.\skills\ffmpeg-bootstrap\scripts\install_ffmpeg_system.ps1
# macOS/Linux:
bash skills/ffmpeg-bootstrap/scripts/install_ffmpeg_system.sh
```

Only useful if ffmpeg is also wanted available system-wide, for tools outside this project — `resolve_ffmpeg_path()` never depends on this being run, and doesn't prefer it over the local/portable copy even if both are present.

## What this skill does NOT do

- Does not transcode, edit, cut, or compose any media itself — pure path-resolution. See `video-assembly-composer` for actual ffmpeg-driven rendering.
- Does not manage ffmpeg version pinning across skills — whichever ffmpeg is resolved is used as-is; a skill needing a specific minimum version must check `ffmpeg -version` output itself.
- Does not install anything without an explicit `uv pip install` step (Python skills' standard bootstrap) or an explicit system-install script run — never a silent background download.

## Bundled files

- `scripts/check_ffmpeg.py` — safe detect, local-portable first, system PATH informational fallback.
- `scripts/resolve_ffmpeg.py` — importable helper (`resolve_ffmpeg_path()`) for other skills.
- `scripts/install_ffmpeg_system.ps1` / `.sh` — OPTIONAL system-wide install via OS package manager.
- `requirements.txt` — `imageio-ffmpeg` (the wheel itself contains the ffmpeg binary).

## Verified

Real test on the project's Windows dev machine (2026-08-05): `uv pip install --python .venv imageio-ffmpeg` installed a ~88MB binary directly at `.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe` — confirmed present on disk, no runtime download triggered. `check_ffmpeg.py` correctly reported `OK (local, portable)` with the resolved path and version line `ffmpeg version 7.1-essentials_build-www.gyan.dev` — a DIFFERENT build/version than the system ffmpeg already on this machine's PATH (`8.1-full_build`), confirming the local copy is genuinely independent, not silently deferring to the system install. `resolve_ffmpeg_path()` correctly returned the local path without touching `shutil.which`.

## Known limitations (v0.2.0)

- The exact ffmpeg build/version bundled inside `imageio-ffmpeg`'s wheel is whatever that package's maintainers ship for a given release — not independently pinned by this skill. If a specific ffmpeg feature/codec is required, verify with `ffmpeg -version`/`-codecs` after resolving, don't assume.
- `install_ffmpeg_system.ps1`'s `winget install Gyan.FFmpeg` requires winget itself present and may prompt a UAC/consent dialog depending on machine policy — this script does not attempt to suppress or auto-approve that prompt. It is optional and not exercised by `resolve_ffmpeg_path()`.
- No version-pinning or minimum-version enforcement across skills that depend on this one — see "What this skill does NOT do".
