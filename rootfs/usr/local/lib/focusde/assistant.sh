#!/usr/bin/env bash
# Focus DE — ouvre l'assistant (Professeur Neuro / SillyTavern) dans la zone Secondaire.
# Ollama + SillyTavern tournent en services systemd ; ici on s'assure que ST répond,
# on déplie la Secondaire si elle est repliée, puis on y place Firefox -> localhost:8000.
set +e
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export SWAYSOCK="${SWAYSOCK:-$(ls "$XDG_RUNTIME_DIR"/sway-ipc.*.sock 2>/dev/null | head -1)}"
LIB="$(cd "$(dirname "$0")" && pwd)"
ST_URL="http://localhost:8000"

# 1) SillyTavern doit répondre (service systemd ; on le (re)démarre si besoin).
if ! curl -s -o /dev/null "$ST_URL"; then
    systemctl --user start sillytavern.service 2>/dev/null
    for _ in $(seq 1 40); do curl -s -o /dev/null "$ST_URL" && break; sleep 1; done
fi

# 2) Si la zone Secondaire existe mais est repliée (scratchpad), la révéler d'abord.
python3 - "$LIB" <<'PY'
import sys, json, subprocess
def get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
wsid = next((w["id"] for w in (get("get_workspaces") or []) if w.get("focused")), None)
if wsid is None:
    sys.exit(0)
mark = "Zs_%d" % wsid
tree = get("get_tree"); scratched = [False]
def walk(n, s):
    if n.get("type") == "workspace" and n.get("name") == "__i3_scratch":
        s = True
    if mark in (n.get("marks") or []):
        scratched[0] = s
    for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
        walk(c, s)
if tree:
    walk(tree, False)
if scratched[0]:                     # secondaire repliée -> l'afficher (toggle = show)
    subprocess.run(["python3", sys.argv[1] + "/secondary_toggle.py"])
PY

# 3) Placer Firefox -> SillyTavern dans la zone Secondaire (profil dédié à l'assistant).
PROF="$HOME/.mozilla/firefox/assistant"
mkdir -p "$PROF"
# Profil "kiosque léger" : pas de page de premier lancement, démarre sur SillyTavern.
if [ ! -f "$PROF/user.js" ]; then
    cat > "$PROF/user.js" <<EOF
user_pref("browser.startup.homepage", "$ST_URL");
user_pref("browser.startup.firstrunSkipsHomepage", true);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("datareporting.policy.firstRunURL", "");
user_pref("browser.messaging-system.whatsNewPanel.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
EOF
fi
python3 "$LIB/activity.py" add secondary env MOZ_ENABLE_WAYLAND=1 firefox-esr \
    --profile "$PROF" --new-window "$ST_URL"
