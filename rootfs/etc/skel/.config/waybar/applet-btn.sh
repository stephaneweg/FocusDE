#!/usr/bin/env bash
export SWAYSOCK=$(ls /run/user/1000/sway-ipc.*.sock 2>/dev/null|head -1)
n=$(swaymsg -t get_workspaces 2>/dev/null | python3 -c 'import sys,json;w=json.load(sys.stdin);print(next((x["name"] for x in w if x.get("focused")),""))')
[ "$n" = "Accueil" ] && exit 0
echo "+ Applet"
