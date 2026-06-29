#!/usr/bin/env bash
# Focus DE - add an application into a zone of the current activity.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_RUNTIME_DIR="$RUN"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export SWAYSOCK="${SWAYSOCK:-$(ls "$RUN"/sway-ipc.*.sock 2>/dev/null | head -1)}"
export MOZ_ENABLE_WAYLAND=1
ZONE="$1"
FF="firefox-esr --profile $HOME/.mozilla/firefox/onyx --new-window"
choice=$(printf 'Firefox\nAbiWord\nGnumeric\nTerminal\nSite web…\n' | fuzzel --dmenu -p "$ZONE > ")
[ -z "$choice" ] && exit 0
case "$choice" in
  Firefox)  python3 "$DIR/activity.py" add "$ZONE" $FF about:blank ;;
  AbiWord)  python3 "$DIR/activity.py" add "$ZONE" abiword ;;
  Gnumeric) python3 "$DIR/activity.py" add "$ZONE" gnumeric ;;
  Terminal) python3 "$DIR/activity.py" add "$ZONE" foot ;;
  "Site web…")
     url=$(printf '' | fuzzel --dmenu -p "URL > ")
     [ -z "$url" ] && exit 0
     case "$url" in http*) ;; *) url="https://$url" ;; esac
     python3 "$DIR/activity.py" add "$ZONE" $FF "$url" ;;
esac
