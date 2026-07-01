#!/usr/bin/env python3
# Focus DE — bouton 🦉 Assistant : l'assistant (Professeur Neuro) est un ONGLET de la
# zone secondaire, repéré PAR ACTIVITÉ via la marque Zasst_<wsid>.
#   - visible           -> on FERME son onglet (historique sauvé sur disque) ; si c'était
#                          la seule app, la secondaire se collapse d'elle-même.
#   - présent mais caché (secondaire repliée) -> on révèle la secondaire.
#   - absent            -> on l'ajoute à la secondaire (en la révélant si repliée).
import os, sys, subprocess
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import zonelib as z

APP = "focus-assistant"

def _ws_node(wsid):
    tree = z.get("get_tree"); res = [None]
    def find(n):
        if n.get("type") == "workspace" and n.get("id") == wsid:
            res[0] = n; return True
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            if find(c):
                return True
        return False
    if tree:
        find(tree)
    return res[0]

def _assistant_ids_in_ws(wsid):
    node = _ws_node(wsid); ids = []
    def w(n):
        if n.get("app_id") == APP:
            ids.append(n["id"])
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            w(c)
    if node:
        w(node)
    return ids

wsid = z.focused_wsid()
if wsid is None:
    sys.exit(0)
A = "Zasst_%d" % wsid
Zs = "Zs_%d" % wsid

if z.visible(A):
    z.sw("[con_mark=%s] kill" % A)                              # fermer l'onglet assistant
elif z.exists(A):
    subprocess.run(["python3", LIB + "/secondary_toggle.py"])  # replié -> révéler la secondaire
else:
    if z.exists(Zs) and not z.visible(Zs):
        subprocess.run(["python3", LIB + "/secondary_toggle.py"])
    subprocess.run(["python3", LIB + "/activity.py", "add", "secondary", "python3", LIB + "/neuro.py"])
    for i in _assistant_ids_in_ws(wsid):                       # marquer l'onglet fraîchement ajouté
        z.sw("[con_id=%d] mark --add %s" % (i, A))
