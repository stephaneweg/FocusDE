#!/usr/bin/env bash
# Install WayVNC so a headless Sway session on the Pi can be viewed and
# controlled remotely (Sway is wlroots-based; WayVNC is the matching VNC server).
set -euo pipefail

echo "==> Installing wayvnc"
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y wayvnc
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm wayvnc
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y wayvnc
else
    echo "Unsupported package manager; install 'wayvnc' manually." >&2
    exit 1
fi

cat <<'EOF'

==> Done. To view the Pi's Sway desktop with no monitor attached:

  ON THE PI (over SSH):
    # Option A — let your normal Sway config start it: add to ~/.config/sway/config
    #     include /path/to/FocusDE/scripts/sway-vnc.conf
    #     and start Sway headless:
    #         WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 sway
    #
    # Option B — one shot:
    #     ./scripts/sway-headless-vnc.sh 1280x720

  ON YOUR MACHINE:
    ssh -L 5900:localhost:5900 <user>@<pi-host>     # tunnel the VNC port
    # then point a VNC client at localhost:5900, e.g.:
    #     vncviewer localhost:5900        (TigerVNC)
    #     or Remmina / RealVNC Viewer

Security: WayVNC is bound to 127.0.0.1, so it is only reachable through the SSH
tunnel — never expose port 5900 on the open network.

Low-latency alternative (to actually *use* it, e.g. games): install 'sunshine'
on the Pi and use the 'moonlight' client — it captures the KMS/Wayland output
and streams with much lower latency than VNC.
EOF
