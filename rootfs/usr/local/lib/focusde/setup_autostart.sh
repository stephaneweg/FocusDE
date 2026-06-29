#!/usr/bin/env bash
# Configure a user to start the Focus DE shell (Sway) automatically on tty1.
# Run as root.   Usage:  sudo ./setup_autostart.sh [username]
# (username defaults to the invoking sudo user.)
set -e

USER_NAME="${1:-${SUDO_USER:-$(logname 2>/dev/null || echo "$USER")}}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
[ -n "$HOME_DIR" ] || { echo "Unknown user: $USER_NAME" >&2; exit 1; }

echo "=== console autologin for '$USER_NAME' on tty1 ==="
# Raspberry Pi OS helper (B2 = console autologin); harmless/no-op elsewhere.
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_boot_behaviour B2 || true
fi

echo "=== ${HOME_DIR}/.bash_profile : start sway on tty1 ==="
PROF="$HOME_DIR/.bash_profile"
[ -f "$PROF" ] || echo '[ -f ~/.profile ] && . ~/.profile' > "$PROF"
if ! grep -q 'exec sway' "$PROF"; then
cat >> "$PROF" <<'EOF'

# Focus DE: start the shell (sway) on the console
if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec sway
fi
EOF
fi
chown "$USER_NAME":"$USER_NAME" "$PROF"

echo "=== done; tail of $PROF ==="
tail -5 "$PROF"
