#!/usr/bin/env python3
# Focus DE - menu deroulant des activites (clic sur le titre dans la barre).
# Liste les activites ouvertes -> clic = bascule. Echap/focus perdu = ferme.
import gi, json, subprocess, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-switcher")

def workspaces():
    try:
        return json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"]))
    except Exception:
        return []

CSS = """
window { background: @surface@; border-radius: 16px; border: 1px solid @border@; }
.title { font-size: 13px; color: @ink_soft@; padding: 4px 6px; }
.act { background: transparent; border: none; border-radius: 10px; padding: 8px 12px; margin: 1px 4px; color: @ink@; font-size: 15px; }
.act:hover { background: @accent@; color: @accent_ink@; }
.act.cur { background: @accent_strong@; color: @accent_ink@; font-weight: bold; }
"""

class Switcher(Gtk.Window):
    def __init__(self):
        super().__init__(title="Activités")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(8)
        self.add(box)
        lab = Gtk.Label(label="Aller à…"); lab.set_xalign(0); lab.get_style_context().add_class("title")
        box.pack_start(lab, False, False, 0)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sc.add(col); box.pack_start(sc, True, True, 0)
        for w in workspaces():
            name = w.get("name", "")
            b = Gtk.Button(label=name); b.get_style_context().add_class("act")
            if w.get("focused"): b.get_style_context().add_class("cur")
            b.set_halign(Gtk.Align.FILL)
            b.get_child().set_xalign(0.0)
            b.connect("clicked", self.go, name)
            col.pack_start(b, False, False, 0)
        self.connect("key-press-event", lambda _w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)
        self.connect("focus-out-event", lambda *_: Gtk.main_quit())

    def go(self, _b, name):
        subprocess.run(["swaymsg", "-q", "workspace " + name]); Gtk.main_quit()

pal = focus_theme.for_activity(focus_theme.focused_ws_name())
prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Switcher(); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
