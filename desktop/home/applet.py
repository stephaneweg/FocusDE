#!/usr/bin/env python3
# Onyx - panneau gauche : applets (horloge + tuiles).
import gi, time, sys
sys.path.insert(0, "/home/maison")
import onyx_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-applet")

CSS = """
window { background: @bg@; }
.clock { font-size: 34px; font-weight: bold; color: @ink@; }
.date  { font-size: 14px; color: @ink_soft@; }
.applet { background: @surface@; border-radius: 14px; border: 1px solid @border@;
          padding: 14px; margin: 6px 4px; }
.applet-title { color: @accent_ink@; font-size: 14px; }
.applet-sub { color: @ink_soft@; font-size: 12px; }
"""

class Applet(Gtk.Window):
    def __init__(self):
        super().__init__(title="Applets")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(22); box.set_margin_start(12); box.set_margin_end(12)
        self.add(box)
        self.clock = Gtk.Label(); self.clock.get_style_context().add_class("clock")
        self.date = Gtk.Label(); self.date.get_style_context().add_class("date")
        box.pack_start(self.clock, False, False, 0)
        box.pack_start(self.date, False, False, 0)
        box.pack_start(Gtk.Label(label=" "), False, False, 6)
        for title, sub in [("Notes", "3 notes"), ("Agenda", "rien aujourd'hui"),
                           ("Musique", "—")]:
            box.pack_start(self.tile(title, sub), False, False, 0)
        self.tick(); GLib.timeout_add_seconds(1, self.tick)

    def tile(self, title, sub):
        f = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        f.get_style_context().add_class("applet")
        t = Gtk.Label(label=title); t.get_style_context().add_class("applet-title"); t.set_xalign(0)
        s = Gtk.Label(label=sub); s.get_style_context().add_class("applet-sub"); s.set_xalign(0)
        f.pack_start(t, False, False, 0); f.pack_start(s, False, False, 0)
        return f

    def tick(self):
        self.clock.set_text(time.strftime("%H:%M"))
        self.date.set_text(time.strftime("%a %d %b"))
        return True

prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(CSS))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Applet(); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
