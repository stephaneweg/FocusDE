#!/usr/bin/env python3
# Focus DE - applique la palette de l'activite au changement de workspace (fluide, sans redemarrage).
import sys, subprocess, json
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme

_last = [None]
def apply_for(name):
    pal = focus_theme.for_activity(name)
    if pal == _last[0]:
        return
    _last[0] = pal
    focus_theme.apply_sway(pal)
    focus_theme.write_waybar(pal)
    focus_theme.reload_waybar()

p = subprocess.Popen(["swaymsg", "-t", "subscribe", "-m", "-r", '["workspace"]'],
                     stdout=subprocess.PIPE, text=True)
dec = json.JSONDecoder(); buf = ""
for line in iter(p.stdout.readline, ""):
    buf += line
    while buf.strip():
        s = buf.lstrip()
        try:
            ev, i = dec.raw_decode(s)
        except ValueError:
            break
        buf = s[i:]
        if isinstance(ev, dict) and ev.get("change") in ("focus", "init"):
            cur = ev.get("current") or {}
            name = cur.get("name")
            if name:
                apply_for(name)
