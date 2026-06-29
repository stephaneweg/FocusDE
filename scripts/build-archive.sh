#!/usr/bin/env bash
# Build a tarball of the payload tree that extracts straight into /.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$HERE/focusde-rootfs.tar.gz}"

tar -C "$HERE/rootfs" --owner=0 --group=0 -czf "$OUT" .

echo "Wrote $OUT"
echo "Install with:  sudo tar -C / -xzf $OUT"
echo "(then seed users from /etc/skel and optionally 'systemctl enable greetd')"
