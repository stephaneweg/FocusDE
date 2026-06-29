#!/usr/bin/env bash
# Install the runtime prerequisites for Focus DE:
#   - Sway shell + bar/launcher/terminal : sway waybar fuzzel foot
#   - login manager                      : greetd (agreety greeter ships with it)
#   - Python GTK (shell + fmtracker)     : python3-gi + GTK 3/4 + Cairo
#   - MIDI synth + GM soundfont          : fluidsynth + fluid-soundfont-gm
#   - hosted apps                        : abiword gnumeric firefox-esr
set -euo pipefail

echo "==> Installing Focus DE prerequisites"

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y \
        sway waybar fuzzel foot greetd \
        python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtk-4.0 \
        fluidsynth fluid-soundfont-gm ffmpeg \
        abiword gnumeric firefox-esr
    echo "    (optional nicer login screen:  sudo apt-get install -y tuigreet)"
else
    cat >&2 <<'EOF'
Unsupported package manager. Install the equivalents of:
  sway waybar fuzzel foot greetd
  python3 + PyGObject (GTK 3 and 4) + Cairo
  fluidsynth + a General-MIDI SoundFont (.sf2)
  abiword gnumeric firefox
EOF
    exit 1
fi

echo "==> Done."
