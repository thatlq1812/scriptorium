# Installs the playwright Python package into the shared venv, then
# downloads the Chromium browser binary (~300MB). HEAVY: real network
# download, real disk usage. Only run this after check_browser.py has
# confirmed something is actually missing -- do not run unconditionally.

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "Installing playwright into the shared venv..."
& "$RepoRoot\skills\python-env-bootstrap\scripts\bootstrap.ps1" -Requirements "$RepoRoot\skills\browser-web-renderer\requirements.txt"

Write-Host "Downloading the Chromium browser binary (this can take a few minutes)..."
& "$RepoRoot\.venv\Scripts\python.exe" -m playwright install chromium

Write-Host ""
Write-Host "Done. Run:"
Write-Host "  .venv\Scripts\python.exe skills\browser-web-renderer\scripts\check_browser.py"
Write-Host "to confirm."
