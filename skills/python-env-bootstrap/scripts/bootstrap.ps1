# Bootstrap a reproducible Python venv for another skill, without assuming
# Python is pre-installed. Uses uv (astral.sh) - a single static binary that
# can install Python itself. Usage:
#   .\bootstrap.ps1 <skill_dir> [python_version]
# <skill_dir> must contain a requirements.txt. Creates <skill_dir>\.venv.
param(
    [Parameter(Mandatory = $true)][string]$SkillDir,
    [string]$PyVersion = "3.12"
)
$ErrorActionPreference = "Stop"

$ReqFile = Join-Path $SkillDir "requirements.txt"
if (-not (Test-Path $ReqFile)) {
    Write-Error "No requirements.txt at $ReqFile"
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found - installing (single static binary, no Python required)..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

uv python install $PyVersion
uv venv "$SkillDir\.venv" --python $PyVersion
uv pip install --python "$SkillDir\.venv" -r $ReqFile

Write-Host "OK: venv ready at $SkillDir\.venv (Python $PyVersion, deps from $ReqFile)"
