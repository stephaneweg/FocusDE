#!/usr/bin/env python3
# Focus DE - collapse/expand de la section SECONDAIRE (droite) via le scratchpad
# (vrai masquage : le primary reprend toute la largeur). Miroir de panel_toggle.py,
# cote droit. La marque Zs_<wsid> porte sur la fenetre dans le conteneur secondaire.
import sys, subprocess, json
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
mark = "Zs_%d" % wsid
node, in_scratch = find_ctx(mark)
if node is None: sys.exit(0)        # pas de section secondaire sur cette activite

if in_scratch:
    # DEPLIER : ramener depuis le scratchpad puis re-ancrer a DROITE (1/3).
    sw("[con_mark=%s] scratchpad show" % mark)
    sw("[con_mark=%s] floating disable" % mark)
    sw("[con_mark=%s] focus" % mark); sw("move down")          # sortir du tabbed du primary
    sw("[con_mark=%s] focus" % mark); sw("focus parent"); sw("layout splith")  # cote a cote
    sw("[con_mark=%s] focus" % mark); sw("split horizontal"); sw("layout tabbed")
    sw("[con_mark=%s] resize set width 33 ppt" % mark)         # secondary = 1/3
else:
    # COLLAPSER : envoyer le conteneur de la section secondaire (onglets compris) au scratchpad.
    sw("[con_mark=%s] focus" % mark); sw("focus parent")
    sw("move scratchpad")
