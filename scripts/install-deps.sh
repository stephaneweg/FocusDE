#!/usr/bin/env bash
# Install the runtime prerequisites for the Focus DE fmtracker:
#   - Python 3 + PyGObject (GTK4 bindings) + Cairo
#   - fluidsynth (the MIDI software synth; renders audio via PipeWire/Pulse/ALSA)
#   - a General-MIDI SoundFont
set -euo pipefail

echo "==> Installing fmtracker prerequisites"

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y \
        python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
        fluidsynth fluid-soundfont-gm
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm \
        python python-gobject gtk4 cairo \
        fluidsynth soundfont-fluid
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y \
        python3 python3-gobject gtk4 \
        fluidsynth fluid-soundfont-gm
else
    echo "Unsupported package manager. Please install manually:" >&2
    echo "  python3, PyGObject (GTK4), fluidsynth, a GM SoundFont (.sf2)" >&2
    exit 1
fi

echo "==> Done."
