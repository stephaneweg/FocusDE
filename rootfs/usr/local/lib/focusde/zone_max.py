#!/usr/bin/env python3
# Onyx - agrandir/restaurer une zone (primary=haut / secondary=bas). Bascule vers 2/3-1/3.
import sys, subprocess, json
def sw(c): subprocess.run(["swaymsg", "-q", c])
def get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
def focused_wsid():
    for w in (get("get_workspaces") or []):
        if w.get("focused"): return w["id"]
    return None
def find_mark(mark):
    tree = get("get_tree"); res = [None]
    def walk(n):
        if mark in (n.get("marks") or []): res[0] = n
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []): walk(c)
    if tree: walk(tree)
    return res[0]

zone = sys.argv[1] if len(sys.argv) > 1 else "primary"
wsid = focused_wsid()
if wsid is None: sys.exit(0)
zs = find_mark("Zs_%d" % wsid); zp = find_mark("Zp_%d" % wsid)
if not zs or not zp: sys.exit(0)            # besoin des 2 zones
hs = zs["rect"]["height"]; hp = zp["rect"]["height"]
total = (hs + hp) or 1
sec = 100.0 * hs / total                     # part actuelle du bas

def set_sec(p):
    sw("[con_mark=Zs_%d] focus" % wsid); sw("resize set height %d ppt" % p)

if zone == "primary":                        # agrandir le HAUT
    if sec < 18:
        set_sec(33)                          # deja maximise -> 2/3-1/3
    else:
        set_sec(6); sw("[con_mark=Zp_%d] focus" % wsid)
else:                                        # agrandir le BAS
    if sec > 55:
        set_sec(33)                          # deja maximise -> 2/3-1/3
    else:
        set_sec(94)
