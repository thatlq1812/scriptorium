#!/usr/bin/env bash
# Bootstrap ONE shared Python venv at the repo root (sibling to skills/),
# without assuming Python is pre-installed. Uses uv (astral.sh) — a single
# static binary that can install Python itself.
#
# All skills share the SAME venv (accumulating installed packages) rather
# than each skill carrying its own .venv/ — avoids duplicating heavy deps
# across every skill folder.
#
# Usage:
#   bootstrap.sh skills/<skill>/requirements.txt [python_version]
set -euo pipefail

REQ_FILE="${1:?Usage: bootstrap.sh <requirements.txt> [python_version]}"
PY_VERSION="${2:-3.12}"

if [ ! -f "$REQ_FILE" ]; then
  echo "No requirements.txt at $REQ_FILE" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PATH="$REPO_ROOT/.venv"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — installing (single static binary, no Python required)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv python install "$PY_VERSION"
if [ ! -d "$VENV_PATH" ]; then
  uv venv "$VENV_PATH" --python "$PY_VERSION"
fi
uv pip install --python "$VENV_PATH" -r "$REQ_FILE"

echo "OK: shared venv ready at $VENV_PATH (Python $PY_VERSION, deps from $REQ_FILE)"
