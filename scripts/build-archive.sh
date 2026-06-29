#!/usr/bin/env bash
# Build a tarball of the payload tree that extracts straight into /.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$HERE/focusde-rootfs.tar.gz}"

# Guard: the Pi's shells choke on CRLF (a stray \r breaks `if … fi`). Keep all
# shipped scripts LF, whatever the dev checkout did.
find "$HERE/rootfs" -name '*.sh' -exec sed -i 's/\r$//' {} + 2>/dev/null || true
sed -i 's/\r$//' "$HERE/rootfs/usr/local/bin/fmtracker" 2>/dev/null || true

tar -C "$HERE/rootfs" --owner=0 --group=0 -czf "$OUT" .

echo "Wrote $OUT"
echo "Install with:  sudo tar -C / -xzf $OUT"
echo "(then seed users from /etc/skel and optionally 'systemctl enable greetd')"
