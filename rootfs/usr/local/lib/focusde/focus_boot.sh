#!/usr/bin/env bash
# Focus DE - robust home build at boot: wait for sway to be ready, then (re)build.
# Launched by sway (exec) -> inherits SWAYSOCK / WAYLAND_DISPLAY.
DIR="$(cd "$(dirname "$0")" && pwd)"
for i in $(seq 1 40); do
  swaymsg -t get_version >/dev/null 2>&1 && break
  sleep 0.5
done
for attempt in 1 2 3; do
  swaymsg -t get_tree 2>/dev/null | grep -q onyx-home && break
  python3 "$DIR/activity.py" home
  # wait (up to ~12s) for the home to actually appear before retrying — a slow
  # headless Pi can take several seconds, and retrying early stacks panels.
  for j in $(seq 1 24); do
    swaymsg -t get_tree 2>/dev/null | grep -q onyx-home && break
    sleep 0.5
  done
done
