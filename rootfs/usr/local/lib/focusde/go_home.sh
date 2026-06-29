#!/usr/bin/env bash
# Focus DE - go back to the home; rebuild it if it disappeared.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_RUNTIME_DIR="$RUN"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export GDK_BACKEND=wayland
export SWAYSOCK="${SWAYSOCK:-$(ls "$RUN"/sway-ipc.*.sock 2>/dev/null | head -1)}"
swaymsg workspace Accueil
if ! swaymsg -t get_tree | grep -q '"app_id": "focus-home"'; then
  swaymsg '[app_id=focus-applet] kill' 2>/dev/null
  python3 "$DIR/activity.py" home
fi
