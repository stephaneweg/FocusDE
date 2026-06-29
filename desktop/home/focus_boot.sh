#!/usr/bin/env bash
# Focus DE - robust home build at boot: wait for sway to be ready, then (re)build.
# Launched by sway (exec) -> inherits SWAYSOCK / WAYLAND_DISPLAY.
DIR="$(cd "$(dirname "$0")" && pwd)"
for i in $(seq 1 40); do
  swaymsg -t get_version >/dev/null 2>&1 && break
  sleep 0.5
done
for i in 1 2 3; do
  if [ "$(swaymsg -t get_tree 2>/dev/null | grep -c onyx-home)" -ge 1 ]; then
    break
  fi
  python3 "$DIR/activity.py" home
  sleep 3
done
