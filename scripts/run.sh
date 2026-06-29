#!/usr/bin/env bash
# Launch the fmtracker straight from the repo (no install needed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/rootfs/usr/local/lib/focusde/apps:${PYTHONPATH:-}"
exec python3 -m fmtracker "$@"
