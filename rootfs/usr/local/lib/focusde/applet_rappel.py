#!/usr/bin/env python3
# Focus DE - applet Rappel (widget embarquable) : prochains rendez-vous.
# Clic sur un RDV / "+ RDV" -> ouvre l'agenda (zone principale) + le dialogue.
import gi, os, subprocess, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
LIBDIR = os.path.dirname(os.path.realpath(__file__))
import focus_theme, focus_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import os; HOME = os.path.expanduser("~")

EXPAND = True
CSS = """
.rappel-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 10px; }
.rappel-head { font-size: 16px; font-weight: bold; color: @ink@; }
.rappel-new { background: @accent@; color: @accent_ink@; border-radius: 10px; padding: 4px 10px; }
.rappel-new:hover { background: @accent_strong@; }
.rappel-day { font-size: 11px; color: @ink_soft@; margin-top: 6px; }
.rappel-evt { background: transparent; border: none; padding: 4px 2px; }
.rappel-evt:hover { background: @accent@; border-radius: 8px; }
.rappel-time { font-size: 13px; font-weight: bold; color: @accent_ink@; }
.rappel-title { font-size: 13px; color: @ink@; }
.rappel-empty { font-size: 12px; color: @ink_soft@; }
"""

class RappelWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("rappel-card"); self.pack_start(card, True, True, 0)
        head = Gtk.Box(spacing=6)
        h = Gtk.Label(label="Rappel"); h.set_xalign(0); h.get_style_context().add_class("rappel-head")
        head.pack_start(h, True, True, 0)
        nb = Gtk.Button(label="+ RDV"); nb.get_style_context().add_class("rappel-new")
        nb.connect("clicked", lambda _w: self.open_agenda(None))
        head.pack_end(nb, False, False, 0); card.pack_start(head, False, False, 0)
        win = Gtk.ScrolledWindow(); win.set_propagate_natural_height(True)
        win.set_min_content_height(60); win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self.box.set_valign(Gtk.Align.START); win.add(self.box); card.pack_start(win, True, True, 0)
        self._mtime = None
        self.refresh(); GLib.timeout_add(1500, self.poll)

    def poll(self):
        try: m = os.path.getmtime(focus_applets.AGENDA_PATH)
        except OSError: m = 0
        if m != self._mtime: self.refresh()
        return True

    def refresh(self):
        try: self._mtime = os.path.getmtime(focus_applets.AGENDA_PATH)
        except OSError: self._mtime = 0
        for c in self.box.get_children(): self.box.remove(c)
        events = focus_applets.upcoming_events(6)
        if not events:
            e = Gtk.Label(label="Aucun rendez-vous.\nCliquez « + RDV »."); e.set_xalign(0)
            e.get_style_context().add_class("rappel-empty"); e.set_line_wrap(True)
            self.box.pack_start(e, False, False, 0); self.box.show_all(); return
        cur = None
        for ev in events:
            if ev["date"] != cur:
                cur = ev["date"]
                d = Gtk.Label(label=focus_applets.fr_date(cur)); d.set_xalign(0)
                d.get_style_context().add_class("rappel-day"); self.box.pack_start(d, False, False, 0)
            self.box.pack_start(self.row(ev), False, False, 0)
        self.box.show_all()

    def row(self, ev):
        b = Gtk.Button(); b.get_style_context().add_class("rappel-evt"); b.set_relief(Gtk.ReliefStyle.NONE)
        h = Gtk.Box(spacing=8)
        tm = Gtk.Label(label=ev.get("time", "")); tm.get_style_context().add_class("rappel-time")
        h.pack_start(tm, False, False, 0)
        ti = Gtk.Label(label=ev["title"]); ti.set_xalign(0); ti.set_ellipsize(3)
        ti.get_style_context().add_class("rappel-title"); h.pack_start(ti, True, True, 0)
        b.add(h); b.connect("clicked", lambda _w: self.open_agenda(ev["id"])); return b

    def open_agenda(self, eid):
        subprocess.Popen(["python3", LIBDIR + "/activity.py", "agenda"],
                         stdin=subprocess.DEVNULL, start_new_session=True)
        cmd = ["python3", LIBDIR + "/event_dialog.py"]
        if eid is not None: cmd += ["--id", str(eid)]
        GLib.timeout_add(700, lambda: (subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                                        start_new_session=True), False)[1])

def make(ctx=None): return RappelWidget(ctx)

if __name__ == "__main__":
    GLib.set_prgname("focus-applet-rappel")
    pal = focus_theme.for_activity(focus_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
