#!/usr/bin/env bash
# A lancer en root (sudo). Configure autologin console + lancement sway + priorite hotspot.
set -e
echo "=== autologin console tty1 (user maison) ==="
raspi-config nonint do_boot_behaviour B2   # B2 = Console Autologin

echo "=== ~/.bash_profile : lancer sway sur tty1 ==="
PROF=/home/maison/.bash_profile
if [ ! -f "$PROF" ]; then
  echo '[ -f ~/.profile ] && . ~/.profile' > "$PROF"
fi
if ! grep -q 'exec sway' "$PROF"; then
cat >> "$PROF" <<'EOF'

# Onyx : lancer le shell (sway) sur la console
if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec sway
fi
EOF
fi
chown maison:maison "$PROF"

echo "=== priorite hotspot Swe (pour revenir dessus au reboot) ==="
nmcli connection modify Swe connection.autoconnect yes
nmcli connection modify Swe connection.autoconnect-priority 20
nmcli connection modify Wegener_Wifi connection.autoconnect-priority 5 2>/dev/null || true

set +e
echo "=== verif ==="
echo "--- .bash_profile ---"; tail -5 "$PROF"
echo -n "--- prio Swe: "; nmcli -t -f connection.autoconnect-priority connection show Swe
echo -n "--- boot behaviour (systemd getty autologin) : "; ls /etc/systemd/system/getty@tty1.service.d/ 2>/dev/null || echo "(via raspi-config)"
echo "=== DONE ==="
