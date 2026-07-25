#!/usr/bin/env bash
# Bootstrap a reproducible Python venv for another skill, without assuming
# Python is pre-installed. Uses uv (astral.sh) — a single static binary that
# can install Python itself. Usage:
#   bootstrap.sh <skill_dir> [python_version]
# <skill_dir> must contain a requirements.txt. Creates <skill_dir>/.venv.
set -euo pipefail

SKILL_DIR="${1:?Usage: bootstrap.sh <skill_dir> [python_version]}"
PY_VERSION="${2:-3.12}"
REQ_FILE="$SKILL_DIR/requirements.txt"

if [ ! -f "$REQ_FILE" ]; then
  echo "No requirements.txt at $REQ_FILE" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — installing (single static binary, no Python required)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv python install "$PY_VERSION"
uv venv "$SKILL_DIR/.venv" --python "$PY_VERSION"
uv pip install --python "$SKILL_DIR/.venv" -r "$REQ_FILE"

echo "OK: venv ready at $SKILL_DIR/.venv (Python $PY_VERSION, deps from $REQ_FILE)"
