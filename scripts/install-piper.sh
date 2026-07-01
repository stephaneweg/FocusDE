#!/usr/bin/env bash
# Focus DE — installe Piper (synthèse vocale neuronale, hors-ligne) + une voix
# française, pour que l'assistant (Professeur Neuro) lise ses réponses à voix haute.
# neuro.py cherche le binaire dans ~/piper/piper/piper et une voix dans ~/piper/voices/*.onnx.
set -e
PIPER_VER="2023.11.14-2"
ARCH="$(uname -m)"                     # aarch64 sur Raspberry Pi 4
DIR="$HOME/piper"
mkdir -p "$DIR/voices"

if [ ! -x "$DIR/piper/piper" ]; then
    echo "==> Piper $PIPER_VER ($ARCH)"
    curl -fsSL "https://github.com/rhasspy/piper/releases/download/$PIPER_VER/piper_linux_${ARCH}.tar.gz" -o /tmp/piper.tgz
    tar -C "$DIR" -xzf /tmp/piper.tgz && rm -f /tmp/piper.tgz
fi

VOICE="fr/fr_FR/tom/medium/fr_FR-tom-medium"     # voix masculine FR, qualité medium
if [ ! -f "$DIR/voices/$(basename "$VOICE").onnx" ]; then
    echo "==> Voix française $(basename "$VOICE")"
    base="https://huggingface.co/rhasspy/piper-voices/resolve/main/$VOICE"
    curl -fsSL "$base.onnx"      -o "$DIR/voices/$(basename "$VOICE").onnx"
    curl -fsSL "$base.onnx.json" -o "$DIR/voices/$(basename "$VOICE").onnx.json"
fi

echo "==> Test :"
echo "Bonjour, je suis le Professeur Neuro." \
    | "$DIR/piper/piper" --model "$DIR/voices/$(basename "$VOICE").onnx" --output_file /tmp/piper_test.wav
aplay -q /tmp/piper_test.wav 2>/dev/null || echo "(pas de sortie audio configurée ici — le son sortira sur le jack/HDMI du Pi)"
echo "==> Piper prêt. L'assistant lit ses réponses automatiquement (bouton 🔊 pour couper)."
