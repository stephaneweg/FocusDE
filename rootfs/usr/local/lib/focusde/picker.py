#!/usr/bin/env python3
# Focus DE - sélecteur d'apps à la souris : choisir la zone + cliquer une app -> ajoutée à la zone.
import gi, subprocess, json, os, glob, re, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-picker")

def sway_get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
def focused_wsid():
    for w in (sway_get("get_workspaces") or []):
        if w.get("focused"): return w["id"]
    return None
def focused_ws_name():
    for w in (sway_get("get_workspaces") or []):
        if w.get("focused"): return w.get("name")
    return None
def slug(n): return re.sub(r'[^a-zA-Z0-9]+', '_', n or "").strip('_') or "act"
def hub_file(n): return os.path.expanduser("~/.config/focus/hubs/%s.list" % slug(n))
def available_zones():
    # le panneau gauche est gere par le gestionnaire d'applets (+ Applet), pas ici.
    return [("primary", "En haut"), ("secondary", "En bas"), ("raccourci", "Raccourci (hub)")]

PRESET = None
if "--zone" in sys.argv:
    _i = sys.argv.index("--zone")
    if _i + 1 < len(sys.argv): PRESET = sys.argv[_i + 1]

def parse_desktop(path):
    name = exec_ = icon = None; nodisplay = False
    try:
        inentry = False
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.rstrip("\n")
            if line.startswith("["):
                inentry = (line == "[Desktop Entry]"); continue
            if not inentry: continue
            if line.startswith("Name=") and not name: name = line[5:]
            elif line.startswith("Exec=") and not exec_: exec_ = line[5:]
            elif line.startswith("Icon=") and not icon: icon = line[5:]
            elif line.startswith("NoDisplay=") and line[10:].strip().lower() == "true": nodisplay = True
    except Exception:
        return None
    if not name or not exec_ or nodisplay: return None
    cmd = re.sub(r'%[a-zA-Z]', '', exec_).strip()
    return {"name": name, "cmd": cmd, "icon": icon or "application-x-executable"}

def list_apps():
    seen = set(); apps = []
    for d in ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]:
        for p in glob.glob(d + "/*.desktop"):
            a = parse_desktop(p)
            if a and a["name"] not in seen:
                seen.add(a["name"]); apps.append(a)
    apps.sort(key=lambda a: a["name"].lower())
    return apps

CSS = """
window { background: @bg@; }
.title { font-size: 17px; font-weight: bold; color: @ink@; }
.zonebtn { border-radius: 12px; padding: 8px 18px; margin: 3px; color: @ink_soft@; background: @border@; }
.zonebtn:checked { background: @accent_strong@; color: @accent_ink@; }
.appbtn { background: @surface@; border-radius: 14px; border: 1px solid @border@; padding: 12px; margin: 6px; }
.appbtn:hover { background: @accent@; border-color: @accent_strong@; }
.appname { font-size: 13px; color: @ink@; }
"""

class Picker(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ajouter une app")
        self.set_default_size(780, 560)
        self.zones = available_zones()
        _ids = [z[0] for z in self.zones]
        self.zone = PRESET if PRESET in _ids else self.zones[0][0]
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(16)
        self.add(box)
        top = Gtk.Box(spacing=8)
        t = Gtk.Label(label="Ajouter dans :"); t.get_style_context().add_class("title")
        top.pack_start(t, False, False, 4)
        grp = None
        for zid, zlabel in self.zones:
            rb = Gtk.RadioButton.new_with_label_from_widget(grp, zlabel)
            if grp is None: grp = rb
            rb.set_mode(False); rb.get_style_context().add_class("zonebtn")
            if zid == self.zone: rb.set_active(True)
            rb.connect("toggled", self.on_zone, zid)
            top.pack_start(rb, False, False, 0)
        close = Gtk.Button(label="✕ Fermer")
        close.connect("clicked", lambda _w: Gtk.main_quit())
        top.pack_end(close, False, False, 0)
        self.connect("key-press-event", self._key)
        box.pack_start(top, False, False, 0)
        self.search = Gtk.SearchEntry(); self.search.set_placeholder_text("Rechercher une app…")
        self.search.connect("search-changed", lambda _w: self.fill())
        box.pack_start(self.search, False, False, 0)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True)
        self.flow = Gtk.FlowBox(); self.flow.set_max_children_per_line(5)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_valign(Gtk.Align.START)
        sc.add(self.flow); box.pack_start(sc, True, True, 0)
        self.apps = list_apps(); self.fill()

    def _key(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape: Gtk.main_quit()

    def on_zone(self, btn, zid):
        if btn.get_active(): self.zone = zid

    def app_btn(self, a):
        b = Gtk.Button(); b.get_style_context().add_class("appbtn")
        b.set_size_request(140, 130); b.set_valign(Gtk.Align.START)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        img = Gtk.Image.new_from_icon_name(a["icon"], Gtk.IconSize.DIALOG)
        nm = Gtk.Label(label=a["name"]); nm.get_style_context().add_class("appname")
        nm.set_line_wrap(True); nm.set_max_width_chars(12); nm.set_justify(Gtk.Justification.CENTER)
        v.pack_start(img, False, False, 0); v.pack_start(nm, False, False, 0)
        b.add(v); b.connect("clicked", self.choose, a)
        return b

    def choose(self, _b, a):
        if self.zone == "raccourci":
            f = hub_file(focused_ws_name())
            os.makedirs(os.path.dirname(f), exist_ok=True)
            with open(f, "a", encoding="utf-8") as fh:
                fh.write("%s\t%s\t%s\n" % (a["name"], a["cmd"], a["icon"]))
        else:
            subprocess.Popen(["python3", os.path.join(os.path.dirname(os.path.realpath(__file__)), "activity.py"), "add", self.zone] + a["cmd"].split())
        Gtk.main_quit()

    def fill(self):
        for c in self.flow.get_children(): self.flow.remove(c)
        q = self.search.get_text().lower()
        for a in self.apps:
            if q and q not in a["name"].lower(): continue
            self.flow.add(self.app_btn(a))
        self.flow.show_all()

prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Picker(); w.connect("destroy", Gtk.main_quit); w.show_all()
GLib.timeout_add(250, lambda: focus_theme.place_floating("focus-picker", 780, 560) or False)
Gtk.main()
