#!/usr/bin/env bash
# Focus DE — ouvre l'assistant (Professeur Neuro) dans la zone Secondaire.
# C'est une petite app GTK (neuro.py) qui parle DIRECTEMENT à Ollama : pas de
# serveur Node, pas de navigateur, aucune config. On déplie la Secondaire si elle
# est repliée, et on y place l'app (ou on la re-focus si elle est déjà ouverte).
set +e
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export SWAYSOCK="${SWAYSOCK:-$(ls "$XDG_RUNTIME_DIR"/sway-ipc.*.sock 2>/dev/null | head -1)}"
LIB="$(cd "$(dirname "$0")" && pwd)"

# Ollama (service systemd) — le démarrer si besoin.
systemctl is-active --quiet ollama 2>/dev/null || systemctl start ollama 2>/dev/null

# Déjà ouvert dans cette activité ? -> révéler la Secondaire si repliée + focus, et sortir.
python3 - "$LIB" <<'PY'
import sys, json, subprocess
def get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
wsid = next((w["id"] for w in (get("get_workspaces") or []) if w.get("focused")), None)
if wsid is None:
    sys.exit(0)
mark = "Zs_%d" % wsid
tree = get("get_tree")
state = {"scratched": False, "assist": False}
def walk(n, s):
    if n.get("type") == "workspace" and n.get("name") == "__i3_scratch":
        s = True
    if mark in (n.get("marks") or []):
        state["scratched"] = s
    if n.get("app_id") == "focus-assistant":
        state["assist"] = True
    for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
        walk(c, s)
if tree:
    walk(tree, False)
if state["scratched"]:
    subprocess.run(["python3", sys.argv[1] + "/secondary_toggle.py"])   # révéler la Secondaire
if state["assist"]:
    subprocess.run(["swaymsg", "-q", "[app_id=focus-assistant] focus"])
    sys.exit(3)   # déjà ouvert -> ne pas relancer
PY
[ $? -eq 3 ] && exit 0

# Sinon : lancer l'app assistant dans la zone Secondaire.
python3 "$LIB/activity.py" add secondary python3 "$LIB/neuro.py"
