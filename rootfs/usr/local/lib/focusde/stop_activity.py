#!/usr/bin/env python3
# Focus DE - confirmation avant d'arreter l'activite courante.
# Lancee par le bouton rouge de la waybar. "Arreter" ferme TOUTES les fenetres de
# l'activite (sway detruit le workspace vide) et revient a l'accueil.
import gi, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-stop")
LIBDIR = os.path.dirname(os.path.realpath(__file__))

name = focus_theme.focused_ws_name() or ""
if not name or name == "Accueil":
    sys.exit(0)   # rien a arreter sur l'accueil

CSS = """
window { background: @surface@; border-radius: 16px; border: 1px solid @border@; }
.q   { font-size: 16px; font-weight: bold; color: @ink@; padding: 6px 4px 2px 4px; }
.sub { font-size: 13px; color: @ink_soft@; padding: 0 4px 10px 4px; }
.cancel { background: @accent@; color: @accent_ink@; border: none; border-radius: 10px; padding: 8px 18px; margin: 4px; }
.cancel:hover { background: @accent_strong@; }
.stop { background: #E5484D; color: #FFFFFF; border: none; border-radius: 10px; padding: 8px 18px; margin: 4px; font-weight: bold; }
.stop:hover { background: #C93B40; }
"""

class Confirm(Gtk.Window):
    def __init__(self):
        super().__init__(title="Arrêter l'activité")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(16)
        self.add(box)
        q = Gtk.Label(label="Arrêter « %s » ?" % name); q.set_xalign(0)
        q.set_line_wrap(True); q.get_style_context().add_class("q")
        s = Gtk.Label(label="Toutes les fenêtres de cette activité seront fermées.")
        s.set_xalign(0); s.set_line_wrap(True); s.get_style_context().add_class("sub")
        box.pack_start(q, False, False, 0); box.pack_start(s, False, False, 0)
        row = Gtk.Box(spacing=6); row.set_halign(Gtk.Align.END)
        c = Gtk.Button(label="Annuler"); c.get_style_context().add_class("cancel")
        c.connect("clicked", lambda _b: Gtk.main_quit())
        k = Gtk.Button(label="Arrêter"); k.get_style_context().add_class("stop")
        k.connect("clicked", self.do_stop)
        row.pack_start(c, False, False, 0); row.pack_start(k, False, False, 0)
        box.pack_start(row, False, False, 0)
        self.connect("key-press-event",
                     lambda _w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)

    def do_stop(self, _b):
        # Detacher l'arret : ce dialogue est lui-meme une fenetre du workspace a fermer,
        # alors on quitte d'abord, puis activity.py stop tue le reste et bascule a l'accueil.
        subprocess.Popen(["python3", LIBDIR + "/activity.py", "stop", name])
        Gtk.main_quit()

pal = focus_theme.for_activity(name)
prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Confirm(); w.connect("destroy", Gtk.main_quit); w.show_all()
GLib.timeout_add(250, lambda: focus_theme.place_floating("focus-stop", 420, 200, borderless=True) or False)
Gtk.main()
