#!/usr/bin/env bash
# Download the legacy FM-Song demo songs (.fms) into a directory.
# Run this ON THE PI to populate the song folder (default /home/maison/fms).
#
# Usage:  ./scripts/install-songs.sh [DEST_DIR]
set -euo pipefail

DEST="${1:-/home/maison/fms}"
API="https://api.github.com/repos/Asher256/asher256-legacy/contents/fmsong/MUSIC"

mkdir -p "$DEST"
echo "==> Fetching .fms song list from $API"

if command -v jq >/dev/null 2>&1; then
    urls=$(curl -fsSL "$API" | jq -r '.[] | select(.name|test("(?i)\.fms$")) | .download_url')
elif command -v python3 >/dev/null 2>&1; then
    urls=$(curl -fsSL "$API" | python3 -c \
        "import sys,json;[print(x['download_url']) for x in json.load(sys.stdin) if x['name'].lower().endswith('.fms')]")
else
    echo "Need 'jq' or 'python3' to parse the listing." >&2
    exit 1
fi

n=0
for u in $urls; do
    fname=$(basename "$u")
    if curl -fsSL "$u" -o "$DEST/$fname"; then
        n=$((n + 1))
    else
        echo "  WARN: failed to fetch $fname" >&2
    fi
done

echo "==> Downloaded $n .fms file(s) to $DEST"
