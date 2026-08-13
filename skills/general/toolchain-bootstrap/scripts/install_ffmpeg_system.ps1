# OPTIONAL, secondary path. The recommended way to get ffmpeg for THIS project
# is the local/portable one: `uv pip install --python .venv -r
# skills\general\toolchain-bootstrap\requirements.txt` (imageio-ffmpeg bundles the actual
# binary inside the wheel, no system install needed). Only run this script if
# you specifically want ffmpeg available system-wide too, for other tools
# outside this project.
$ErrorActionPreference = "Stop"

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "ffmpeg already on PATH - nothing to do."
    exit 0
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install winget (ships with Windows 10 1809+/11), or just use the local/portable install instead (see requirements.txt)."
    exit 1
}

winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements

Write-Host "Done. Open a new shell (PATH refresh) and run check_ffmpeg.py to verify (it still prefers the local/portable copy if present)."
