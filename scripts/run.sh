#!/usr/bin/env bash
# Launch the fmtracker straight from the repo (no install needed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/app:${PYTHONPATH:-}"
exec python3 -m fmtracker "$@"
