#!/usr/bin/env python3
# Focus DE — bouton Secondaire : replie/déplie la zone secondaire (droite, 1/3), en
# exclusion mutuelle avec l'assistant.
#   - visible -> on la replie ; et on réaffiche l'assistant s'il existe.
#   - cachée  -> on replie l'assistant s'il est visible, puis on affiche la secondaire.
import os, sys
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import zonelib as z

wsid = z.focused_wsid()
if wsid is None:
    sys.exit(0)
Zs = "Zs_%d" % wsid
Za = "Za_%d" % wsid
if not z.exists(Zs):
    sys.exit(0)                       # pas de section secondaire

if z.visible(Zs):
    z.hide(Zs)
    if z.exists(Za):
        z.dock_right(Za)              # rendre la place à l'assistant
else:
    if z.visible(Za):
        z.hide(Za)                    # libérer le slot droit
    z.dock_right(Zs)
