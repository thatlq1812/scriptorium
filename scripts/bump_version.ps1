# scripts/bump_version.ps1 -- Bump Scriptorium repo version (YY.MM.NN scheme)
#
# Scheme (thatlq1812 decision 2026-08-15, matching scriptorium_workspace's own scheme):
# <2-digit year>.<2-digit month>.<sequence>, where the sequence resets to 01 the moment
# the year OR month changes, and otherwise increments by 1.
#   26.08.01 -> 26.08.02   (same month, another release today)
#   26.08.42 -> 26.09.01   (new month -- reset)
#   26.12.03 -> 27.01.01   (new year -- reset)
#
# Single source of truth: VERSION (repo root, plain text, one line). This is a
# repo/release version -- independent from each skill's own per-skill semver in
# registry/skills.json (bumped separately, when a skill's own SKILL.md content
# changes meaningfully; see registry/SCHEMA.md). Bump this one when cutting a
# release snapshot of skills/ + registry/, not when editing a single skill.
#
# Run standalone: .\scripts\bump_version.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT        = (Get-Item $PSScriptRoot).Parent.FullName
$VersionFile = "$ROOT\VERSION"

function Log([string]$msg)  { Write-Host "[bump-version] $msg" -ForegroundColor Cyan }
function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

if (-not (Test-Path $VersionFile)) { Fail "Required file missing: $VersionFile" }

$Current = (Get-Content $VersionFile -Raw).Trim()
if ($Current -notmatch '^(\d{2})\.(\d{2})\.(\d+)$') {
    Fail "Current version '$Current' doesn't match the YY.MM.NN scheme -- fix it manually first, then re-run."
}
$CurYear, $CurMonth, $CurSeq = $Matches[1], $Matches[2], [int]$Matches[3]

$TodayYear  = (Get-Date).ToString("yy")
$TodayMonth = (Get-Date).ToString("MM")

if ($CurYear -eq $TodayYear -and $CurMonth -eq $TodayMonth) {
    $NewSeq = $CurSeq + 1
} else {
    $NewSeq = 1
}
$NewVersion = "{0}.{1}.{2:D2}" -f $TodayYear, $TodayMonth, $NewSeq

if ($NewVersion -eq $Current) {
    Log "Version unchanged ($Current)."
    Write-Output $Current
    return
}

Log "Bumping version: $Current -> $NewVersion"
Set-Content -Path $VersionFile -Value $NewVersion -NoNewline -Encoding UTF8
Add-Content -Path $VersionFile -Value "" -NoNewline -Encoding UTF8

Log "Updated VERSION -> $NewVersion"
Write-Output $NewVersion
