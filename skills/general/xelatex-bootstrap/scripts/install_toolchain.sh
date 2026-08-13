#!/usr/bin/env bash
# Installs the XeLaTeX toolchain (xelatex + biber + texlive-lang-vietnamese)
# via the platform's package manager. HEAVY: downloads/installs a large
# package set, takes several minutes. Only run this after
# check_toolchain.py has confirmed something is actually missing -- do not
# run unconditionally.
set -euo pipefail

os="$(uname -s)"

if [[ "$os" == "Darwin" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew not found. Install from https://brew.sh, or install MacTeX manually from https://www.tug.org/mactex/" >&2
        exit 1
    fi
    echo "Installing MacTeX (no-GUI) via brew (this can take several minutes)..."
    brew install --cask mactex-no-gui
elif [[ "$os" == "Linux" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installing texlive-xetex + texlive-lang-vietnamese + biber via apt (needs sudo)..."
        sudo apt-get update
        sudo apt-get install -y texlive-xetex texlive-lang-vietnamese biber fonts-noto
    else
        echo "No known package manager (apt-get) found on this Linux distro. Install XeLaTeX/biber manually." >&2
        exit 1
    fi
else
    echo "Unrecognized OS: $os. Install XeLaTeX/biber manually." >&2
    exit 1
fi

echo ""
echo "Done. Run:"
echo "  python3 skills/general/xelatex-bootstrap/scripts/check_toolchain.py"
echo "to confirm xelatex/biber/fontspec are now detected."
