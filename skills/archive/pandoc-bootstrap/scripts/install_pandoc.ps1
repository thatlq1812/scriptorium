# Installs pandoc via winget. Only run this after check_pandoc.py has
# confirmed it's actually missing -- do not run unconditionally.

$ErrorActionPreference = "Stop"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install pandoc manually from https://pandoc.org/installing.html"
    exit 1
}

Write-Host "Installing pandoc via winget..."
winget install --id JohnMacFarlane.Pandoc -e --accept-package-agreements --accept-source-agreements

Write-Host ""
Write-Host "Done. Open a NEW terminal (PATH needs to refresh), then run:"
Write-Host "  python skills\general\pandoc-bootstrap\scripts\check_pandoc.py"
