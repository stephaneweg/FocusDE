#!/usr/bin/env python3
# Focus DE - palettes partagees + theme courant / par activite.
import os, re, subprocess
CONF = os.path.expanduser("~/.config/focus")

PALETTES = {
    "Lavande": dict(bg="#F3F1FA", surface="#FFFFFF", ink="#2C2A38", ink_soft="#8A86A0",
                    border="#E4DEF3", accent="#DCD3F2", accent_strong="#C9BEEA",
                    accent_ink="#4B3FA0", avatar="#D4537E"),
    "Menthe":  dict(bg="#EAF6F0", surface="#FFFFFF", ink="#22403A", ink_soft="#7C998F",
                    border="#D6EFE4", accent="#BDE9D6", accent_strong="#9FE1C6",
                    accent_ink="#0F6E56", avatar="#1D9E75"),
    "Pêche":   dict(bg="#FBEFE9", surface="#FFFFFF", ink="#4A2E22", ink_soft="#A88B7E",
                    border="#F3DDD2", accent="#F8D3C2", accent_strong="#F2BBA3",
                    accent_ink="#993C1D", avatar="#D85A30"),
    "Ciel":    dict(bg="#E9F1FB", surface="#FFFFFF", ink="#22344A", ink_soft="#7E91A8",
                    border="#D6E4F4", accent="#C3DCF5", accent_strong="#A6C8EE",
                    accent_ink="#185FA5", avatar="#378ADD"),
    "Fraise":  dict(bg="#FCEEF1", surface="#FFFFFF", ink="#4A1F2A", ink_soft="#A8808C",
                    border="#F3D9E0", accent="#F8C9D6", accent_strong="#EFA8BC",
                    accent_ink="#99355A", avatar="#D4537E"),
    "Cassis":  dict(bg="#F4EEF7", surface="#FFFFFF", ink="#3A2240", ink_soft="#988AA0",
                    border="#E6D9EC", accent="#DCC8E6", accent_strong="#C3A8D2",
                    accent_ink="#6A2C8A", avatar="#8E3CA8"),
    "Blé":     dict(bg="#FAF4E4", surface="#FFFFFF", ink="#43381F", ink_soft="#A89A78",
                    border="#EFE6C8", accent="#F2E2A6", accent_strong="#E3C766",
                    accent_ink="#7E5E0B", avatar="#BA7517"),
    "Océan":   dict(bg="#E6F1F5", surface="#FFFFFF", ink="#163139", ink_soft="#77919A",
                    border="#CFE5EA", accent="#AEDDE6", accent_strong="#7CC6D6",
                    accent_ink="#0F5C73", avatar="#2090A8"),
    "Forêt":   dict(bg="#E9F2EA", surface="#FFFFFF", ink="#1B3A26", ink_soft="#789083",
                    border="#D5E7D9", accent="#BFE0C8", accent_strong="#8FC9A2",
                    accent_ink="#1E6E3C", avatar="#27772E"),
    "Agrume":  dict(bg="#F4F7E4", surface="#FFFFFF", ink="#36400F", ink_soft="#92A06B",
                    border="#E6EFC4", accent="#DCEFA0", accent_strong="#C2E061",
                    accent_ink="#5E7011", avatar="#7FAE17"),
    "Corail":  dict(bg="#FCEEEA", surface="#FFFFFF", ink="#4A271E", ink_soft="#B08A80",
                    border="#F6D8CF", accent="#FAC9B8", accent_strong="#F2A88E",
                    accent_ink="#B24A2C", avatar="#E5613A"),
    "Moka":    dict(bg="#F3ECE3", surface="#FFFFFF", ink="#3A2C20", ink_soft="#A1907E",
                    border="#E6D8C8", accent="#DEC9AE", accent_strong="#C7A982",
                    accent_ink="#6E4A28", avatar="#8A5A33"),
    "Coucher de soleil": dict(bg="#FCEDE8", surface="#FFFFFF", ink="#46282E", ink_soft="#AE8888",
                    border="#F5D8CE", accent="#F9CDB6", accent_strong="#F0A9A0",
                    accent_ink="#C24A55", avatar="#EE7E5A"),
    "Lilas":   dict(bg="#F6EFF8", surface="#FFFFFF", ink="#3C2A44", ink_soft="#9C8AA4",
                    border="#EAD9EE", accent="#E6CCEE", accent_strong="#D2AADE",
                    accent_ink="#8A3CA0", avatar="#B45AC8"),
    "Brume":   dict(bg="#EEF0F3", surface="#FFFFFF", ink="#2E343C", ink_soft="#8A929C",
                    border="#DDE2E8", accent="#D2D9E2", accent_strong="#B4BFCC",
                    accent_ink="#4A5663", avatar="#6E7B8A"),
    "Glacier": dict(bg="#ECF4F8", surface="#FFFFFF", ink="#1E333D", ink_soft="#7E939E",
                    border="#D7E7EE", accent="#CDE6F0", accent_strong="#A6D0E0",
                    accent_ink="#2E6E86", avatar="#4AA0C0"),
    "Ardoise": dict(bg="#2A2A33", surface="#3A3A46", ink="#ECEAF2", ink_soft="#9C9CB0",
                    border="#45454F", accent="#4C4866", accent_strong="#615C82",
                    accent_ink="#CFC8EE", avatar="#7C6FE0"),
    "Nuit":    dict(bg="#1B2233", surface="#27314A", ink="#E6ECF5", ink_soft="#94A0B8",
                    border="#33405C", accent="#3A4A6E", accent_strong="#4E6492",
                    accent_ink="#A9C2F0", avatar="#3A7BD5"),
    "Encre":   dict(bg="#161618", surface="#242428", ink="#ECECF0", ink_soft="#9A9AA4",
                    border="#33333A", accent="#2E2E48", accent_strong="#4A4A78",
                    accent_ink="#9D8CFF", avatar="#7C6FE0"),
}
ORDER = ["Lavande", "Lilas", "Cassis", "Fraise", "Corail", "Coucher de soleil", "Pêche",
         "Blé", "Moka", "Agrume", "Menthe", "Forêt", "Océan", "Glacier", "Ciel", "Brume",
         "Ardoise", "Nuit", "Encre"]
TILE_COLORS = ["#7C6FE0", "#1D9E75", "#D85A30", "#378ADD", "#2E9E5B", "#C2497E"]

def slug(n): return re.sub(r'[^a-zA-Z0-9]+', '_', n or "").strip('_') or "act"

def place_floating(app_id, w, h, x=None, y=None, borderless=False):
    # `for_window [app_id=...]` misses at map time for GTK3 (the app_id is published
    # just after the first map), so a floating tool re-applies its placement itself
    # once its window is mapped.
    pos = ("position %d %d" % (x, y)) if x is not None else "position center"
    bn = "border none, " if borderless else ""
    subprocess.run(["swaymsg",
                    '[app_id="%s"] floating enable, %sresize set width %d height %d, move %s'
                    % (app_id, bn, w, h, pos)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def current():
    try:
        v = open(CONF + "/theme").read().strip()
        if v in PALETTES: return v
    except Exception:
        pass
    return "Lavande"

def focused_ws_name():
    # nom de l'activite (workspace) en cours ; None si indisponible.
    try:
        import json
        for w in json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"])):
            if w.get("focused"): return w.get("name")
    except Exception:
        pass
    return None

def for_activity(name):
    try:
        v = open(CONF + "/themes/" + slug(name)).read().strip()
        if v in PALETTES: return v
    except Exception:
        pass
    return current()

def colors(pal=None):
    return PALETTES.get(pal or current(), PALETTES["Lavande"])

def css(template, pal=None):
    # remplace les jetons @cle@ par les couleurs de la palette, renvoie des bytes pour GTK.
    c = colors(pal)
    for k, v in c.items():
        template = template.replace("@%s@" % k, v)
    return template.encode()

# --- application a sway + waybar (runtime) ---
def _sw(c): subprocess.run(["swaymsg", "-q", c])

def apply_sway(pal=None):
    C = colors(pal)
    _sw("output * bg %s solid_color" % C["bg"])
    _sw("client.focused %s %s %s %s %s" % (C["accent_strong"], C["accent"], C["accent_ink"], C["accent"], C["accent_strong"]))
    _sw("client.focused_inactive %s %s %s %s %s" % (C["border"], C["bg"], C["ink_soft"], C["bg"], C["border"]))
    _sw("client.unfocused %s %s %s %s %s" % (C["border"], C["bg"], C["ink_soft"], C["bg"], C["border"]))

WAYBAR_STYLE = """* { font-family: "Sans"; font-size: 14px; border: none; min-height: 0; }
window#waybar { background: %(bg)s; color: %(accent_ink)s; }
#custom-activity { font-size: 17px; font-weight: bold; color: %(ink)s; padding: 0 20px; }
#custom-stop { background: #E5484D; color: #FFFFFF; border-radius: 12px; padding: 4px 14px; margin: 6px 8px; font-weight: bold; }
#custom-stop:hover { background: #C93B40; }
#custom-add { background: %(accent)s; color: %(accent_ink)s; border-radius: 12px; padding: 4px 16px; margin: 6px 4px; }
#custom-add:hover { background: %(accent_strong)s; }
#custom-applet { background: %(accent)s; color: %(accent_ink)s; border-radius: 12px; padding: 4px 14px; margin: 6px 4px; }
#custom-applet:hover { background: %(accent_strong)s; }
#custom-panel { background: %(accent)s; color: %(accent_ink)s; border-radius: 12px; padding: 4px 12px; margin: 6px 4px; }
#custom-panel:hover { background: %(accent_strong)s; }
#custom-secondary { background: %(accent)s; color: %(accent_ink)s; border-radius: 12px; padding: 4px 12px; margin: 6px 4px; }
#custom-secondary:hover { background: %(accent_strong)s; }
#custom-home { background: %(accent)s; color: %(accent_ink)s; border-radius: 12px; padding: 4px 18px; margin: 6px 8px; }
#custom-home:hover { background: %(accent_strong)s; }
#clock { color: %(ink_soft)s; padding: 0 16px; }
"""

def write_waybar(pal=None):
    p = os.path.expanduser("~/.config/waybar/style.css")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(WAYBAR_STYLE % colors(pal))

def reload_waybar():
    subprocess.run(["pkill", "-SIGUSR2", "waybar"])  # recharge le style sans redemarrer
