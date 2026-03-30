#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/install_with_pip.sh         # install runtime package (editable)
#   ./scripts/install_with_pip.sh --dev   # install runtime + dev dependencies
#
# Optional env override:
#   PYTHON_BIN=/path/to/python3 ./scripts/install_with_pip.sh --dev

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

INSTALL_TARGET="-e ."
if [[ "${1:-}" == "--dev" ]]; then
  INSTALL_TARGET="-e .[dev]"
fi

echo "Using python: $PYTHON_BIN"
echo "Project root: $PROJECT_ROOT"
echo "Installing with pip target: $INSTALL_TARGET"

cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install $INSTALL_TARGET

echo "Installation complete."
echo "You can now run:"
echo "  ./arxiv_bot.py -help"
echo "  arxiv-bot -help"
