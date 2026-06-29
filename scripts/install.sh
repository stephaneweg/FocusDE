#!/usr/bin/env bash
# Install Focus DE: lay the payload tree onto / and seed the current user.
# Run as root.   Usage:  sudo ./scripts/install.sh [--login] [username]
#   --login   enable the greetd login manager (shows a login, then starts Sway)
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Run as root:  sudo $0 $*" >&2; exit 1; }

HERE="$(cd "$(dirname "$0")/.." && pwd)"
ENABLE_LOGIN=0
USER_NAME=""
for a in "$@"; do
    case "$a" in
        --login) ENABLE_LOGIN=1 ;;
        *)       USER_NAME="$a" ;;
    esac
done
USER_NAME="${USER_NAME:-${SUDO_USER:-root}}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"

echo "==> Laying payload onto /"
cp -a "$HERE/rootfs/." /
chmod +x /usr/local/bin/fmtracker /usr/local/lib/focusde/*.sh 2>/dev/null || true

if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    echo "==> Seeding config for current user '$USER_NAME' -> $USER_HOME/.config"
    mkdir -p "$USER_HOME/.config"
    cp -a /etc/skel/.config/. "$USER_HOME/.config/"
    for sub in sway waybar focus fuzzel; do
        [ -e "$USER_HOME/.config/$sub" ] && chown -R "$USER_NAME":"$USER_NAME" "$USER_HOME/.config/$sub"
    done
fi

if [ "$ENABLE_LOGIN" -eq 1 ]; then
    echo "==> Enabling greetd login manager"
    systemctl disable getty@tty1.service 2>/dev/null || true
    systemctl enable greetd.service
fi

cat <<EOF

==> Done.
  Code:   /usr/local/lib/focusde  (+ apps/fmtracker, launcher /usr/local/bin/fmtracker)
  Skel:   /etc/skel/.config       (every NEW user gets Focus DE automatically)
  User:   ${USER_HOME:-<none>}/.config
  Login:  $( [ "$ENABLE_LOGIN" -eq 1 ] && echo "greetd enabled (Sway after login)" || echo "rerun with --login for greetd, or log in on tty1 and run 'sway'" )
EOF
