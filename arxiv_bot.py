#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer the pinned project environment when available.
if [[ -x "/opt/anaconda3/envs/openai311/bin/python3" ]]; then
  PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    exec /opt/anaconda3/envs/openai311/bin/python3 "$SCRIPT_DIR/scripts/arxiv_bot_entry.py" "$@"
fi

PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
  exec python3 "$SCRIPT_DIR/scripts/arxiv_bot_entry.py" "$@"
