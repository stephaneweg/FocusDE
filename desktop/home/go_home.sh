#!/usr/bin/env bash
# Onyx - revenir a l'accueil ; reconstruit le home s'il a disparu.
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-1 GDK_BACKEND=wayland
export SWAYSOCK=$(ls /run/user/1000/sway-ipc.*.sock 2>/dev/null | head -1)
swaymsg workspace Accueil
if ! swaymsg -t get_tree | grep -q '"app_id": "onyx-home"'; then
  swaymsg '[app_id=onyx-applet] kill' 2>/dev/null
  python3 /home/maison/activity.py home
fi
