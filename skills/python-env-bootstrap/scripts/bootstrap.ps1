# Bootstrap ONE shared Python venv at the repo root (sibling to skills/),
# without assuming Python is pre-installed. Uses uv (astral.sh) - a single
# static binary that can install Python itself.
#
# All skills share the SAME venv (accumulating installed packages) rather
# than each skill carrying its own .venv/ -- avoids duplicating heavy deps
# (e.g. torch, pulled in by both document-ai-structurer and any future ML
# skill) across every skill folder.
#
# Usage:
#   .\bootstrap.ps1 -Requirements skills\<skill>\requirements.txt [-PyVersion 3.12]
param(
    [Parameter(Mandatory = $true)][string]$Requirements,
    [string]$PyVersion = "3.12"
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Requirements)) {
    Write-Error "No requirements.txt at $Requirements"
    exit 1
}

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent | Split-Path -Parent
$VenvPath = Join-Path $RepoRoot ".venv"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found - installing (single static binary, no Python required)..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

uv python install $PyVersion
if (-not (Test-Path $VenvPath)) {
    uv venv $VenvPath --python $PyVersion
}
uv pip install --python $VenvPath -r $Requirements

Write-Host "OK: shared venv ready at $VenvPath (Python $PyVersion, deps from $Requirements)"
