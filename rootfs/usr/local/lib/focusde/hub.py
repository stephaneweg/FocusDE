#!/usr/bin/env python3
# Onyx - hub d'activite : grille d'apps. Mode categorie (Travailler...) ou --custom <activite>
# (raccourcis stockes dans ~/.config/onyx/hubs/<slug>.list : lignes "name\tcmd\ticon").
import gi, subprocess, os, glob, re, sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-hub")
import os; HOME = os.path.expanduser("~")
LIBDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIBDIR)
import onyx_theme

CATMAP = {
    "Travailler": ["Office", "Finance", "WordProcessor", "Spreadsheet"],
    "Apprendre":  ["Education"],
    "Jouer":      ["Game"],
    # Création = graphisme + audio/musique. On inclut les catégories d'AUTORING
    # freedesktop (pas juste les principales)…
    "Créer":      ["Graphics", "2DGraphics", "RasterGraphics", "VectorGraphics",
                   "3DGraphics", "Photography", "Publishing", "Art",
                   "AudioVideo", "Audio", "Music", "AudioVideoEditing",
                   "Sequencer", "Midi", "Recorder", "Mixer"],
}
# …et on EXCLUT les fonctions de consommation : un visualiseur/lecteur n'est pas
# un outil de création (freedesktop les marque "Viewer"/"Player").
CATEXCLUDE = {"Créer": {"Viewer", "Player"}}

def slug(name): return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_') or "act"
def hub_file(name): return os.path.expanduser("~/.config/onyx/hubs/%s.list" % slug(name))

def parse(path):
    name = ex = icon = None; nod = False; cats = ""
    try:
        ine = False
        for l in open(path, encoding="utf-8", errors="ignore"):
            l = l.rstrip("\n")
            if l.startswith("["): ine = (l == "[Desktop Entry]"); continue
            if not ine: continue
            if l.startswith("Name=") and not name: name = l[5:]
            elif l.startswith("Exec=") and not ex: ex = l[5:]
            elif l.startswith("Icon=") and not icon: icon = l[5:]
            elif l.startswith("Categories="): cats = l[11:]
            elif l.startswith("NoDisplay=") and l[10:].strip().lower() == "true": nod = True
    except Exception:
        return None
    if not name or not ex or nod: return None
    return {"name": name, "cmd": re.sub(r'%[a-zA-Z]', '', ex).strip(),
            "icon": icon or "application-x-executable",
            "cats": set(c for c in cats.split(";") if c)}

def apps_for(cat):
    want = set(CATMAP.get(cat, [])); block = CATEXCLUDE.get(cat, set())
    seen = set(); out = []
    for d in ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]:
        for p in glob.glob(d + "/*.desktop"):
            a = parse(p)
            if a and (a["cats"] & want) and not (a["cats"] & block) and a["name"] not in seen:
                seen.add(a["name"]); out.append(a)
    out.sort(key=lambda a: a["name"].lower()); return out

def custom_apps(name):
    out = []
    try:
        for line in open(hub_file(name), encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                out.append({"name": p[0], "cmd": p[1], "icon": p[2] if len(p) > 2 else "application-x-executable"})
    except FileNotFoundError:
        pass
    return out

CSS = """
window { background: @bg@; }
.htitle { font-size: 22px; font-weight: bold; color: @ink@; }
.empty { font-size: 15px; color: @ink_soft@; }
.appbtn { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 16px; margin: 8px; }
.appbtn:hover { background: @accent@; border-color: @accent_strong@; }
.appname { font-size: 14px; color: @ink@; }
"""

class Hub(Gtk.Window):
    def __init__(self, cat, custom_name=None):
        super().__init__(title=custom_name or cat)
        self.cat = cat; self.custom_name = custom_name; self._mtime = -1
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(24)
        self.add(box)
        t = Gtk.Label(label=custom_name or cat); t.set_xalign(0); t.get_style_context().add_class("htitle")
        box.pack_start(t, False, False, 0)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True)
        self.flow = Gtk.FlowBox(); self.flow.set_max_children_per_line(6)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_valign(Gtk.Align.START)
        sc.add(self.flow); box.pack_start(sc, True, True, 0)
        self.refresh()
        if custom_name is not None:
            GLib.timeout_add_seconds(2, self.poll)

    def get_apps(self):
        if self.custom_name is not None: return custom_apps(self.custom_name)
        return apps_for(self.cat)

    def refresh(self):
        for c in self.flow.get_children(): self.flow.remove(c)
        apps = self.get_apps()
        if not apps and self.custom_name is not None:
            l = Gtk.Label(label="Aucun raccourci pour le moment.\nAjoute des apps avec le bouton « + » en haut → « Raccourci ».")
            l.get_style_context().add_class("empty"); l.set_justify(Gtk.Justification.CENTER)
            self.flow.add(l)
        for a in apps:
            self.flow.add(self.tile(a))
        self.flow.show_all()

    def poll(self):
        try: m = os.path.getmtime(hub_file(self.custom_name))
        except OSError: m = 0
        if m != self._mtime:
            self._mtime = m; self.refresh()
        return True

    def tile(self, a):
        b = Gtk.Button(); b.get_style_context().add_class("appbtn")
        b.set_size_request(150, 150); b.set_valign(Gtk.Align.START)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        img = Gtk.Image.new_from_icon_name(a["icon"], Gtk.IconSize.DIALOG); img.set_pixel_size(56)
        nm = Gtk.Label(label=a["name"]); nm.get_style_context().add_class("appname")
        nm.set_line_wrap(True); nm.set_max_width_chars(12); nm.set_justify(Gtk.Justification.CENTER)
        v.pack_start(img, False, False, 0); v.pack_start(nm, False, False, 0); b.add(v)
        b.connect("clicked", lambda _w, cmd=a["cmd"]:
                  subprocess.Popen(["python3", LIBDIR + "/activity.py", "add", "primary"] + cmd.split()))
        return b

args = sys.argv[1:]
if args and args[0] == "--custom":
    cname = " ".join(args[1:]) or "Activité"; pal = onyx_theme.for_activity(cname)
    w = Hub(None, custom_name=cname)
else:
    cname = args[0] if args else "Travailler"; pal = onyx_theme.current()
    w = Hub(cname)
prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
