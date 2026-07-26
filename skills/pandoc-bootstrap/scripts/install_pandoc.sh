#!/usr/bin/env bash
# Installs pandoc via the platform's package manager. Only run this after
# check_pandoc.py has confirmed it's actually missing -- do not run
# unconditionally.
set -euo pipefail

os="$(uname -s)"

if [[ "$os" == "Darwin" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew not found. Install pandoc manually from https://pandoc.org/installing.html" >&2
        exit 1
    fi
    echo "Installing pandoc via brew..."
    brew install pandoc
elif [[ "$os" == "Linux" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installing pandoc via apt (needs sudo)..."
        sudo apt-get update
        sudo apt-get install -y pandoc
    else
        echo "No known package manager (apt-get) found on this Linux distro. Install pandoc manually." >&2
        exit 1
    fi
else
    echo "Unrecognized OS: $os. Install pandoc manually from https://pandoc.org/installing.html" >&2
    exit 1
fi

echo ""
echo "Done. Run:"
echo "  python3 skills/pandoc-bootstrap/scripts/check_pandoc.py"
