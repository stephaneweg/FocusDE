#!/usr/bin/env python3
# Focus DE — helpers partagés pour les zones repliables de droite (secondaire & assistant).
# Les deux occupent le MÊME slot droit (1/3) en exclusion mutuelle : afficher l'une replie
# l'autre au scratchpad, et la refermer réaffiche l'autre si elle existe. Marques :
#   Zs_<wsid> = secondaire   |   Za_<wsid> = assistant (Professeur Neuro)
import json, subprocess, time

def sw(c):
    subprocess.run(["swaymsg", "-q", c])

def get(t):
    try:
        return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception:
        return None

def focused_wsid():
    for w in (get("get_workspaces") or []):
        if w.get("focused"):
            return w["id"]
    return None

def _find(mark):
    """(existe, sous_scratchpad) pour la marque donnée."""
    tree = get("get_tree")
    res = [False, False]
    def walk(n, scratch):
        if n.get("type") == "workspace" and n.get("name") == "__i3_scratch":
            scratch = True
        if mark in (n.get("marks") or []):
            res[0] = True
            res[1] = scratch
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            walk(c, scratch)
    if tree:
        walk(tree, False)
    return res[0], res[1]

def exists(mark):
    return _find(mark)[0]

def visible(mark):
    e, scratched = _find(mark)
    return e and not scratched

def hide(mark):
    """Replie la zone (son conteneur) au scratchpad."""
    sw("[con_mark=%s] focus" % mark)
    sw("focus parent")
    sw("move scratchpad")

def dock_right(mark):
    """Rappelle la zone du scratchpad et la ré-ancre à droite (1/3)."""
    sw("[con_mark=%s] scratchpad show" % mark)
    sw("[con_mark=%s] floating disable" % mark)
    sw("[con_mark=%s] focus" % mark); sw("move down")
    sw("[con_mark=%s] focus" % mark); sw("focus parent"); sw("layout splith")
    sw("[con_mark=%s] focus" % mark); sw("split horizontal"); sw("layout tabbed")
    sw("[con_mark=%s] resize set width 33 ppt" % mark)
