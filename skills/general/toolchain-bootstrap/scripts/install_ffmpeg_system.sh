#!/usr/bin/env bash
# OPTIONAL, secondary path. The recommended way to get ffmpeg for THIS project
# is the local/portable one: `uv pip install --python .venv -r
# skills/general/toolchain-bootstrap/requirements.txt` (imageio-ffmpeg bundles the actual
# binary inside the wheel, no system install needed). Only run this script if
# you specifically want ffmpeg available system-wide too, for other tools
# outside this project. (macOS: brew, Debian/Ubuntu: apt-get, Fedora/RHEL: dnf, Arch: pacman.)
set -euo pipefail

if command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg already on PATH - nothing to do."
    exit 0
fi

if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y ffmpeg
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm ffmpeg
else
    echo "No known package manager (brew/apt-get/dnf/pacman) found on PATH." >&2
    echo "Just use the local/portable install instead (see requirements.txt)." >&2
    exit 1
fi

echo "Done. Run check_ffmpeg.py to verify (it still prefers the local/portable copy if present)."
