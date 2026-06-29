#!/usr/bin/env bash
# Onyx - construction robuste de l'accueil au boot : attendre sway pret, puis (re)construire.
# Lance par sway (exec) -> herite de SWAYSOCK / WAYLAND_DISPLAY.
for i in $(seq 1 40); do
  swaymsg -t get_version >/dev/null 2>&1 && break
  sleep 0.5
done
for i in 1 2 3; do
  if [ "$(swaymsg -t get_tree 2>/dev/null | grep -c onyx-home)" -ge 1 ]; then
    break
  fi
  python3 /home/maison/activity.py home
  sleep 3
done
