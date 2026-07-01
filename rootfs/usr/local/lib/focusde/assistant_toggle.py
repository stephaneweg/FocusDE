#!/usr/bin/env python3
# Focus DE — bouton 🦉 Assistant : ouvre/ferme le Professeur Neuro dans le slot de droite,
# en exclusion mutuelle avec la zone secondaire.
#   - visible        -> on le replie ; et on réaffiche le secondaire s'il existe.
#   - caché / absent -> on replie le secondaire s'il est visible, puis on affiche
#                       l'assistant (ré-ancrage s'il existe déjà, sinon on le lance).
import os, sys, subprocess
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import zonelib as z

wsid = z.focused_wsid()
if wsid is None:
    sys.exit(0)
Za = "Za_%d" % wsid
Zs = "Zs_%d" % wsid

if z.visible(Za):
    z.hide(Za)
    if z.exists(Zs):
        z.dock_right(Zs)                       # rendre la place au secondaire
else:
    if z.visible(Zs):
        z.hide(Zs)                             # libérer le slot droit
    if z.exists(Za):
        z.dock_right(Za)                       # réafficher l'assistant existant
    else:                                      # première fois : lancer Neuro comme zone "assistant"
        subprocess.run(["python3", LIB + "/activity.py", "add", "assistant",
                        "python3", LIB + "/neuro.py"])
