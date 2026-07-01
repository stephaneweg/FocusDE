#!/usr/bin/env python3
# Focus DE — bouton Secondaire : replie/déplie la zone secondaire (droite, 1/3), avec
# tout son contenu (y compris l'onglet assistant s'il y est).
import os, sys
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import zonelib as z

wsid = z.focused_wsid()
if wsid is None:
    sys.exit(0)
Zs = "Zs_%d" % wsid
if not z.exists(Zs):
    sys.exit(0)                       # pas de section secondaire

if z.visible(Zs):
    z.hide(Zs)
else:
    z.dock_right(Zs)
