#!/usr/bin/env bash
# Install the Focus DE Sway shell system-wide:
#   - shared code   -> /usr/local/lib/focusde/
#   - default config -> /etc/skel/.config/   (every NEW user gets it automatically)
#   - and into the current user's ~/.config/  (so it works right away)
#
# Run as root.   Usage:  sudo ./scripts/install-desktop.sh [--autostart] [username]
#
# Prerequisites (install separately): sway waybar fuzzel foot python3-gi
# gir1.2-gtk-3.0 abiword gnumeric firefox-esr.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root:  sudo $0 $*" >&2
    exit 1
fi

HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/desktop"
LIB=/usr/local/lib/focusde

AUTOSTART=0
USER_NAME=""
for arg in "$@"; do
    case "$arg" in
        --autostart) AUTOSTART=1 ;;
        *)           USER_NAME="$arg" ;;
    esac
done
USER_NAME="${USER_NAME:-${SUDO_USER:-root}}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"

echo "==> Installing shared code -> $LIB"
mkdir -p "$LIB"
cp "$SRC"/home/*.py "$SRC"/home/*.sh "$SRC"/home/*.json "$LIB"/
chmod +x "$LIB"/*.sh
chmod 644 "$LIB"/*.py "$LIB"/*.json

install_config() {   # $1 = target .config dir
    local cfg="$1"
    mkdir -p "$cfg"
    cp -r "$SRC"/config/* "$cfg"/
    chmod +x "$cfg"/waybar/*.sh 2>/dev/null || true
}

echo "==> Installing default config -> /etc/skel/.config (future users)"
install_config /etc/skel/.config

if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    echo "==> Installing config for current user '$USER_NAME' -> $USER_HOME/.config"
    install_config "$USER_HOME/.config"
    for sub in sway waybar onyx fuzzel; do
        chown -R "$USER_NAME":"$USER_NAME" "$USER_HOME/.config/$sub"
    done
fi

if [ "$AUTOSTART" -eq 1 ]; then
    echo "==> Enabling autostart (sway on tty1) for '$USER_NAME'"
    "$LIB/setup_autostart.sh" "$USER_NAME"
fi

cat <<EOF

==> Done.
    Code:        $LIB
    New users:   /etc/skel/.config  (sway, waybar, onyx, fuzzel)
    Current user:$( [ -n "$USER_HOME" ] && echo " $USER_HOME/.config" || echo " (skipped)")

  Start the shell:  log in on tty1 and run 'sway'
  (or re-run with --autostart to launch it automatically at boot).
EOF
