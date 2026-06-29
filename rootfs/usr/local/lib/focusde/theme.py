#!/usr/bin/env python3
# Focus DE - selecteur de theme : echantillons de palettes, clic = applique.
import gi, subprocess, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
LIBDIR = os.path.dirname(os.path.realpath(__file__))
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-theme")
import os; HOME = os.path.expanduser("~")

def focused_ws():
    try:
        for w in json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"])):
            if w.get("focused"): return w.get("name")
    except Exception:
        pass
    return None

CSS_T = """
window { background: @bg@; }
.title { font-size: 18px; font-weight: bold; color: @ink@; }
.modebtn { border-radius: 12px; padding: 6px 16px; margin: 3px; color: @ink_soft@; background: @border@; }
.modebtn:checked { background: @accent_strong@; color: @accent_ink@; }
.swatch { border-radius: 16px; border: 2px solid @border@; margin: 8px; }
.swatch:hover { border-color: @accent_strong@; }
.swname { font-size: 14px; color: @ink@; }
"""

def chip(color):
    c = Gtk.Box(); c.set_size_request(24, 24)
    p = Gtk.CssProvider(); p.load_from_data(("box{background:%s;border-radius:12px;}" % color).encode())
    c.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    return c

class ThemeSel(Gtk.Window):
    def __init__(self):
        super().__init__(title="Thème")
        self.set_default_size(840, 600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(18)
        self.add(box)
        t = Gtk.Label(label="Choisir un thème"); t.set_xalign(0); t.get_style_context().add_class("title")
        box.pack_start(t, False, False, 0)
        self.mode = "global"; self.actname = focused_ws() or ""
        moderow = Gtk.Box(spacing=8)
        hasact = self.actname and self.actname != "Accueil"
        grp = None
        for mid, lbl in [("global", "Partout"),
                         ("activity", "Cette activité" + ((" (%s)" % self.actname) if hasact else ""))]:
            rb = Gtk.RadioButton.new_with_label_from_widget(grp, lbl)
            if grp is None: grp = rb
            rb.set_mode(False); rb.get_style_context().add_class("modebtn")
            rb.set_sensitive(mid == "global" or hasact)
            rb.connect("toggled", self.on_mode, mid)
            moderow.pack_start(rb, False, False, 0)
        box.pack_start(moderow, False, False, 0)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True)
        flow = Gtk.FlowBox(); flow.set_max_children_per_line(5)
        flow.set_selection_mode(Gtk.SelectionMode.NONE); flow.set_valign(Gtk.Align.START)
        sc.add(flow); box.pack_start(sc, True, True, 0)
        cur = focus_theme.current()
        for name in focus_theme.ORDER:
            flow.add(self.swatch(name, name == cur))

    def swatch(self, name, iscur):
        C = focus_theme.colors(name)
        b = Gtk.Button(); b.get_style_context().add_class("swatch"); b.set_size_request(150, 130)
        p = Gtk.CssProvider(); p.load_from_data(("button.swatch{background:%s;}" % C["bg"]).encode())
        b.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "bottom"): getattr(v, "set_margin_" + m)(14)
        chips = Gtk.Box(spacing=6); chips.set_halign(Gtk.Align.CENTER)
        for key in ("accent", "accent_strong", "avatar"):
            chips.pack_start(chip(C[key]), False, False, 0)
        v.pack_start(chips, False, False, 0)
        nm = Gtk.Label(label=(("✓ " if iscur else "") + name)); nm.get_style_context().add_class("swname")
        v.pack_start(nm, False, False, 0)
        b.add(v)
        b.connect("clicked", lambda _w, n=name: self.apply(n))
        return b

    def on_mode(self, btn, mid):
        if btn.get_active(): self.mode = mid

    def apply(self, name):
        if self.mode == "activity" and self.actname and self.actname != "Accueil":
            subprocess.Popen(["python3", LIBDIR + "/theme_apply.py", "--activity", self.actname, name])
        else:
            subprocess.Popen(["python3", LIBDIR + "/theme_apply.py", name])
        Gtk.main_quit()

prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS_T))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = ThemeSel(); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
