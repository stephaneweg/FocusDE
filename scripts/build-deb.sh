#!/usr/bin/env bash
# Build a .deb of Focus DE from the payload tree (rootfs/).
# Usage:  ./scripts/build-deb.sh [VERSION]      (default 0.1.0)
# Requires: dpkg-deb (run on Debian/Ubuntu/Raspberry Pi OS or WSL).
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
VER="${1:-0.1.0}"
STAGE="$(mktemp -d)/focusde_${VER}_all"

mkdir -p "$STAGE"
cp -a "$HERE/rootfs/." "$STAGE/"
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Keep scripts LF — a stray CRLF breaks the shells.
find "$STAGE" -name '*.sh' -exec sed -i 's/\r$//' {} + 2>/dev/null || true
sed -i 's/\r$//' "$STAGE/usr/local/bin/fmtracker" 2>/dev/null || true

# Normalise permissions (source may be a Windows/exFAT checkout where all is 0777).
find "$STAGE" -type d -exec chmod 0755 {} +
find "$STAGE" -type f -exec chmod 0644 {} +

mkdir -p "$STAGE/DEBIAN"
sed "s/@VERSION@/$VER/" "$HERE/packaging/debian/control" > "$STAGE/DEBIAN/control"
printf 'Installed-Size: %s\n' "$(du -sk "$STAGE" | cut -f1)" >> "$STAGE/DEBIAN/control"
install -m 0755 "$HERE/packaging/debian/postinst" "$STAGE/DEBIAN/postinst"

# Executable bits inside the payload (git modes are lost when built from a tarball).
chmod 0755 "$STAGE/usr/local/bin/fmtracker" "$STAGE/usr/local/lib/focusde/"*.sh
chmod 0755 "$STAGE/etc/skel/.config/waybar/"*.sh 2>/dev/null || true

OUT="$HERE/focusde_${VER}_all.deb"
dpkg-deb --root-owner-group --build "$STAGE" "$OUT"
rm -rf "$(dirname "$STAGE")"
echo "Built $OUT"
