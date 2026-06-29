#!/usr/bin/env bash
# Launch Sway with the headless (no-monitor) backend and a VNC server, so the
# Raspberry Pi's graphical Sway session can be viewed/controlled remotely even
# with no display attached.
#
# Usage:   ./scripts/sway-headless-vnc.sh [WIDTHxHEIGHT]   (default 1280x720)
# Then, from your machine:
#       ssh -L 5900:localhost:5900 <user>@<pi>
#       <your VNC client> localhost:5900
set -euo pipefail

RES="${1:-1280x720}"
export WLR_BACKENDS=headless
export WLR_LIBINPUT_NO_DEVICES=1
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

echo "==> Starting headless Sway (${RES})"
sway ${SWAY_CONFIG:+-c "$SWAY_CONFIG"} &
SWAY_PID=$!

# Wait for the Sway IPC socket to come up.
for _ in $(seq 1 50); do
    swaymsg -t get_version >/dev/null 2>&1 && break
    sleep 0.2
done

swaymsg output HEADLESS-1 resolution "$RES" position 0,0 || true

echo "==> Starting wayvnc on 127.0.0.1:5900 (tunnel in over SSH)"
wayvnc 127.0.0.1 5900 &

trap 'kill "$SWAY_PID" 2>/dev/null || true' EXIT
wait "$SWAY_PID"
