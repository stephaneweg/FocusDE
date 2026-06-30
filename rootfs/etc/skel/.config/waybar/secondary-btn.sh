#!/usr/bin/env bash
# Focus DE - bouton "Secondaire" : visible seulement si l'activite courante a une
# section secondaire (marque Zs_<wsid>, qu'elle soit affichee ou repliee au scratchpad).
export SWAYSOCK=$(ls /run/user/1000/sway-ipc.*.sock 2>/dev/null|head -1)
wsid=$(swaymsg -t get_workspaces 2>/dev/null | python3 -c 'import sys,json;w=json.load(sys.stdin);print(next((x["id"] for x in w if x.get("focused")),0))')
[ "$wsid" = "0" ] && exit 0
swaymsg -t get_marks 2>/dev/null | python3 -c "import sys,json;m=json.load(sys.stdin);print('Secondaire' if 'Zs_$wsid' in m else '')"
