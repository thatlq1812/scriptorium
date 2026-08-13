# Installs MiKTeX (XeLaTeX + biber) via winget. HEAVY: downloads/installs
# several hundred MB, takes several minutes. Only run this after
# check_xelatex.py has confirmed something is actually missing -- do not
# run unconditionally. MiKTeX installs missing LaTeX packages (fontspec,
# polyglossia...) on the fly on first compile by default, so no separate
# package-install step is scripted here.

$ErrorActionPreference = "Stop"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install MiKTeX manually from https://miktex.org/download"
    exit 1
}

Write-Host "Installing MiKTeX via winget (this can take several minutes)..."
winget install --id MiKTeX.MiKTeX -e --accept-package-agreements --accept-source-agreements

Write-Host ""
Write-Host "Done. Open a NEW terminal (PATH needs to refresh), then run:"
Write-Host "  python skills\general\toolchain-bootstrap\scripts\check_xelatex.py"
Write-Host "to confirm xelatex/biber/fontspec are now detected."
