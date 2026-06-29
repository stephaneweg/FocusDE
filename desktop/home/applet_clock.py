#!/usr/bin/env python3
# Onyx / Focus DE - applet Horloge (widget embarquable dans panel_host).
import gi, time, datetime, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import onyx_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

EXPAND = False
CSS = """
.clock-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 14px 10px; }
.clock-time { font-size: 40px; font-weight: bold; color: @ink@; }
.clock-date { font-size: 14px; color: @ink_soft@; }
"""

class ClockWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.get_style_context().add_class("clock-card")
        self.t = Gtk.Label(); self.t.get_style_context().add_class("clock-time")
        self.d = Gtk.Label(); self.d.get_style_context().add_class("clock-date")
        self.d.set_line_wrap(True); self.d.set_justify(Gtk.Justification.CENTER)
        card.pack_start(self.t, False, False, 0); card.pack_start(self.d, False, False, 0)
        self.pack_start(card, True, True, 0)
        self.tick(); GLib.timeout_add_seconds(1, self.tick)

    def tick(self):
        self.t.set_text(time.strftime("%H:%M"))
        n = datetime.datetime.now()
        s = "%s %d %s" % (JOURS[n.weekday()], n.day, MOIS[n.month - 1])
        self.d.set_text(s[0].upper() + s[1:]); return True

def make(ctx=None): return ClockWidget(ctx)

if __name__ == "__main__":
    GLib.set_prgname("onyx-applet-clock")
    pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
