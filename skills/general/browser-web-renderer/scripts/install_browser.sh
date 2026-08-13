#!/usr/bin/env bash
# Installs the playwright Python package into the shared venv, then
# downloads the Chromium browser binary (~300MB). HEAVY: real network
# download, real disk usage. Only run this after check_browser.py has
# confirmed something is actually missing -- do not run unconditionally.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

echo "Installing playwright into the shared venv..."
bash "$repo_root/skills/general/toolchain-bootstrap/scripts/bootstrap.sh" "$repo_root/skills/general/browser-web-renderer/requirements.txt"

echo "Downloading the Chromium browser binary (this can take a few minutes)..."
"$repo_root/.venv/bin/python" -m playwright install chromium

echo ""
echo "Done. Run:"
echo "  .venv/bin/python skills/general/browser-web-renderer/scripts/check_browser.py"
echo "to confirm."
