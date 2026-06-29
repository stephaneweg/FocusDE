#!/usr/bin/env bash
# Full install: prerequisites + a user launcher + a desktop entry.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT/scripts/install-deps.sh"

BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$BIN_DIR" "$DESKTOP_DIR"

cat > "$BIN_DIR/fmtracker" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/app:\${PYTHONPATH:-}"
exec python3 -m fmtracker "\$@"
EOF
chmod +x "$BIN_DIR/fmtracker"

cat > "$DESKTOP_DIR/fmtracker.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FM-Song Tracker
Comment=MIDI music tracker (fluidsynth)
Exec=$BIN_DIR/fmtracker
Terminal=false
Categories=AudioVideo;Audio;Music;
EOF

echo "==> Installed launcher at $BIN_DIR/fmtracker"
echo "    (make sure $BIN_DIR is on your PATH)"
