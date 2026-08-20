# scripts/cut_release.ps1 -- Mechanical tail of a release cut: bump VERSION, commit, tag, push.
#
# Deliberately does NOT commit your actual content changes -- commit those yourself first (a real
# commit message describing what changed), then run this script purely for the repeatable,
# opinion-free part: bump -> "Bump VERSION to X for release cut" commit -> tag X -> push both.
# Refuses on a dirty working tree so it's never accidentally the thing that commits unrelated
# work under a generic release message.
#
# Consuming apps (e.g. scriptorium_workspace) pin an exact tag from this repo -- see that repo's
# docs/BUILD_AND_RELEASE.md and scripts/pin_skills_ref.ps1. After this script pushes a new tag,
# go bump the pin there.
#
# Run from repo root: .\scripts\cut_release.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Get-Item $PSScriptRoot).Parent.FullName

function Log([string]$msg)  { Write-Host "[cut-release] $msg" -ForegroundColor Cyan }
function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }
function Ok([string]$msg)   { Write-Host "[ok]   $msg" -ForegroundColor Green }

Push-Location $ROOT
try {
    $Dirty = git status --porcelain
    if ($Dirty) {
        Fail "Working tree not clean -- commit your real content changes first (with a real message describing them), then re-run this script for just the version bump/tag/push. Dirty files:`n$Dirty"
    }

    $Branch = git branch --show-current
    if (-not $Branch) { Fail "Could not determine current branch (detached HEAD?)." }

    Log "Bumping version..."
    & "$PSScriptRoot\bump_version.ps1" | Out-Null
    $NewVersion = (Get-Content "$ROOT\VERSION" -Raw).Trim()
    Ok "VERSION -> $NewVersion"

    git add VERSION
    git commit -m "Bump VERSION to $NewVersion for release cut" | Out-Null
    Ok "Committed version bump."

    git tag $NewVersion
    Ok "Tagged $NewVersion"

    Log "Pushing $Branch + tag $NewVersion to origin..."
    git push origin $Branch
    if ($LASTEXITCODE -ne 0) { Fail "git push (branch) failed." }
    git push origin $NewVersion
    if ($LASTEXITCODE -ne 0) { Fail "git push (tag) failed." }

    Ok "Released $NewVersion. In a consuming app, run: .\scripts\pin_skills_ref.ps1 -Ref $NewVersion"
} finally {
    Pop-Location
}
