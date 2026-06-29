#!/usr/bin/env python3
# Onyx / Focus DE - gestionnaire d'applets : cocher les VRAIS applets du panneau gauche.
# "Appliquer" enregistre la selection et reconstruit le panneau (une fenetre panel_host).
import gi, subprocess, json, sys
sys.path.insert(0, "/home/maison")
import onyx_theme, onyx_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-applets")
HOME = "/home/maison"

def focused():
    try:
        for w in json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"])):
            if w.get("focused"): return w.get("name"), w.get("id")
    except Exception:
        pass
    return None, None

CSS = """
window { background: @bg@; }
.title { font-size: 18px; font-weight: bold; color: @ink@; }
.appname { font-size: 15px; color: @ink@; }
.appdesc { font-size: 12px; color: @ink_soft@; }
.apply { background: @accent_strong@; color: @accent_ink@; border-radius: 12px; padding: 8px 20px; font-weight: bold; }
.apply:hover { background: @accent@; }
list, row { background: @bg@; }
"""

class Mgr(Gtk.Window):
    def __init__(self):
        super().__init__(title="Applets")
        self.set_default_size(460, 460)
        self.wsname, self.wsid = focused()
        sel = set(onyx_applets.load_applet_sel(self.wsname))
        self.apps = onyx_applets.APPLETS
        self.state = [a["id"] in sel for a in self.apps]
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(16)
        self.add(box)
        head = Gtk.Box(spacing=8)
        t = Gtk.Label(label="Applets du panneau gauche"); t.set_xalign(0)
        t.get_style_context().add_class("title")
        head.pack_start(t, True, True, 0)
        cl = Gtk.Button(label="✕"); cl.connect("clicked", lambda _w: Gtk.main_quit())
        head.pack_end(cl, False, False, 0)
        box.pack_start(head, False, False, 0)
        lb = Gtk.ListBox(); lb.set_selection_mode(Gtk.SelectionMode.NONE)
        for i, a in enumerate(self.apps):
            row = Gtk.Box(spacing=12); row.set_margin_top(6); row.set_margin_bottom(6)
            row.set_margin_start(6); row.set_margin_end(6)
            cb = Gtk.CheckButton(); cb.set_active(self.state[i]); cb.set_valign(Gtk.Align.CENTER)
            cb.connect("toggled", self._toggle, i)
            row.pack_start(cb, False, False, 0)
            row.pack_start(Gtk.Image.new_from_icon_name(a["icon"], Gtk.IconSize.DND), False, False, 0)
            txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            nm = Gtk.Label(label=a["name"]); nm.set_xalign(0); nm.get_style_context().add_class("appname")
            ds = Gtk.Label(label=a["desc"]); ds.set_xalign(0); ds.set_line_wrap(True)
            ds.get_style_context().add_class("appdesc")
            txt.pack_start(nm, False, False, 0); txt.pack_start(ds, False, False, 0)
            row.pack_start(txt, True, True, 0)
            lb.add(row)
        box.pack_start(lb, True, True, 0)
        ap = Gtk.Button(label="Appliquer"); ap.get_style_context().add_class("apply")
        ap.connect("clicked", lambda _w: self.apply())
        box.pack_start(ap, False, False, 0)
        self.connect("key-press-event", lambda _w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)

    def _toggle(self, cb, i):
        self.state[i] = cb.get_active()

    def apply(self):
        ids = [self.apps[i]["id"] for i in range(len(self.apps)) if self.state[i]]
        onyx_applets.save_applet_sel(self.wsname, ids)
        subprocess.Popen(["python3", HOME + "/activity.py", "panel"],
                         stdin=subprocess.DEVNULL, start_new_session=True)
        Gtk.main_quit()

pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Mgr(); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
