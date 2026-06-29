#!/usr/bin/env bash
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-1
export SWAYSOCK=$(ls /run/user/1000/sway-ipc.*.sock 2>/dev/null | head -1)
export MOZ_ENABLE_WAYLAND=1
ZONE="$1"
FF="firefox-esr --profile /home/maison/.mozilla/firefox/onyx --new-window"
choice=$(printf 'Firefox\nAbiWord\nGnumeric\nTerminal\nSite web…\n' | fuzzel --dmenu -p "$ZONE > ")
[ -z "$choice" ] && exit 0
case "$choice" in
  Firefox)  python3 /home/maison/activity.py add "$ZONE" $FF about:blank ;;
  AbiWord)  python3 /home/maison/activity.py add "$ZONE" abiword ;;
  Gnumeric) python3 /home/maison/activity.py add "$ZONE" gnumeric ;;
  Terminal) python3 /home/maison/activity.py add "$ZONE" foot ;;
  "Site web…")
     url=$(printf '' | fuzzel --dmenu -p "URL > ")
     [ -z "$url" ] && exit 0
     case "$url" in http*) ;; *) url="https://$url" ;; esac
     python3 /home/maison/activity.py add "$ZONE" $FF "$url" ;;
esac
