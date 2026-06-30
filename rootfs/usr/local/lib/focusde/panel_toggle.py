#!/usr/bin/env python3
# Focus DE - collapse/expand du panneau gauche : on le cache via le scratchpad (vrai masquage).
import sys, subprocess, json, os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from activity import pop_left          # sortie fiable a gauche (vs "move left" en nb fixe)
def sw(c): subprocess.run(["swaymsg", "-q", c])
def get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
def focused_wsid():
    for w in (get("get_workspaces") or []):
        if w.get("focused"): return w["id"]
    return None
def find_ctx(mark):
    tree = get("get_tree"); res = [None, False]
    def walk(n, scratch):
        if n.get("type") == "workspace" and n.get("name") == "__i3_scratch":
            scratch = True
        if mark in (n.get("marks") or []):
            res[0] = n; res[1] = scratch
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            walk(c, scratch)
    if tree: walk(tree, False)
    return res

wsid = focused_wsid()
if wsid is None: sys.exit(0)
mark = "Zl_%d" % wsid
node, in_scratch = find_ctx(mark)
if node is None: sys.exit(0)        # pas de panneau gauche

if in_scratch:
    # deplier : ramener la fenetre du scratchpad + la re-tiler a gauche
    sw("[con_mark=%s] scratchpad show" % mark)
    sw("[con_mark=%s] floating disable" % mark)
    sw("[con_mark=%s] focus" % mark)
    pop_left("con_mark=%s" % mark)      # sortir du tabbed quel que soit le nb d'onglets
    sw("[con_mark=%s] split vertical" % mark)   # colonne en pile (comme a la construction)
    sw("[con_mark=%s] resize set width 240 px" % mark)
else:
    # plier : envoyer la seule fenetre du panneau au scratchpad
    sw("[con_mark=%s] move scratchpad" % mark)
