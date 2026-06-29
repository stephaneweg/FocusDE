#!/usr/bin/env python3
# Onyx - applique la palette de l'activite au changement de workspace (fluide, sans redemarrage).
import sys, subprocess, json
sys.path.insert(0, "/home/maison")
import onyx_theme

_last = [None]
def apply_for(name):
    pal = onyx_theme.for_activity(name)
    if pal == _last[0]:
        return
    _last[0] = pal
    onyx_theme.apply_sway(pal)
    onyx_theme.write_waybar(pal)
    onyx_theme.reload_waybar()

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
