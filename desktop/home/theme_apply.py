#!/usr/bin/env python3
# theme_apply.py <Palette>                  -> GLOBAL (persiste + reconstruit l'accueil)
#                --swayonly                  -> boot : re-applique la palette courante a sway
#                --activity <nom> <Palette>  -> override pour une activite (persiste + applique)
import sys, os, subprocess, time, json
sys.path.insert(0, "/home/maison")
import onyx_theme
CONF = os.path.expanduser("~/.config/onyx")

def sw(c): subprocess.run(["swaymsg", "-q", c])
def focused():
    try:
        for w in json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"])):
            if w.get("focused"): return w.get("name")
    except Exception:
        pass
    return None

a = sys.argv[1:]

if a and a[0] == "--swayonly":
    onyx_theme.apply_sway()
    sys.exit(0)

if a and a[0] == "--activity":
    name = a[1]
    pal = a[2] if len(a) > 2 else onyx_theme.current()
    if pal not in onyx_theme.PALETTES: pal = "Lavande"
    os.makedirs(CONF + "/themes", exist_ok=True)
    open(CONF + "/themes/" + onyx_theme.slug(name), "w").write(pal)
    onyx_theme.apply_sway(pal); onyx_theme.write_waybar(pal); onyx_theme.reload_waybar()
    print("activite %s -> %s" % (name, pal))
    sys.exit(0)

pal = a[0] if a else onyx_theme.current()
if pal not in onyx_theme.PALETTES: pal = "Lavande"
os.makedirs(CONF, exist_ok=True)
open(CONF + "/theme", "w").write(pal)
onyx_theme.apply_sway(pal); onyx_theme.write_waybar(pal); onyx_theme.reload_waybar()
cur = focused()
sw("workspace Accueil")
sw("[app_id=onyx-home] kill"); sw("[app_id=onyx-applet] kill"); time.sleep(1)
subprocess.run(["python3", "/home/maison/activity.py", "home"]); time.sleep(1)
if cur and cur != "Accueil":
    sw("workspace " + cur)
print("global -> %s" % pal)
