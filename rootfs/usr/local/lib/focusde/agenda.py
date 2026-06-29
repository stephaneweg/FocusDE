#!/usr/bin/env python3
# Focus DE - app Agenda (zone principale). Vue Liste + vue Mois (calendrier).
# Clic sur un rdv = modifier ; "+ Nouveau" = creer ; double-clic sur un jour = creer ce jour-la.
import gi, os, subprocess, sys, datetime
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
LIBDIR = os.path.dirname(os.path.realpath(__file__))
import focus_theme, focus_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-agenda")
import os; HOME = os.path.expanduser("~")

CSS = """
window { background: @bg@; }
.h1 { font-size: 26px; font-weight: bold; color: @ink@; }
.day { font-size: 14px; font-weight: bold; color: @accent_ink@; margin-top: 10px; }
.new { background: @accent_strong@; color: @accent_ink@; border-radius: 12px; padding: 8px 18px; font-weight: bold; }
.new:hover { background: @accent@; }
.evt { background: @surface@; border-radius: 14px; border: 1px solid @border@; padding: 12px 14px; margin: 4px 0; }
.evt:hover { background: @accent@; }
.time { font-size: 16px; font-weight: bold; color: @accent_ink@; }
.etitle { font-size: 16px; color: @ink@; }
.enote { font-size: 12px; color: @ink_soft@; }
.empty { font-size: 15px; color: @ink_soft@; }
calendar { background: @surface@; color: @ink@; border-radius: 14px; border: 1px solid @border@;
           padding: 8px; font-size: 16px; }
calendar:selected { background: @accent_strong@; color: @accent_ink@; border-radius: 8px; }
calendar.highlight { color: @accent_ink@; font-weight: bold; }
"""

class Agenda(Gtk.Window):
    def __init__(self):
        super().__init__(title="Agenda")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(outer, "set_margin_" + m)(24)
        self.add(outer)
        head = Gtk.Box(spacing=10)
        t = Gtk.Label(label="Agenda"); t.set_xalign(0); t.get_style_context().add_class("h1")
        head.pack_start(t, True, True, 0)
        self.stack = Gtk.Stack(); self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        sw = Gtk.StackSwitcher(); sw.set_stack(self.stack); head.pack_start(sw, False, False, 0)
        nb = Gtk.Button(label="+ Nouveau"); nb.get_style_context().add_class("new")
        nb.connect("clicked", lambda _w: self.edit(None)); head.pack_end(nb, False, False, 0)
        outer.pack_start(head, False, False, 0)
        outer.pack_start(self.stack, True, True, 0)

        # --- vue Liste ---
        lsc = Gtk.ScrolledWindow(); lsc.set_vexpand(True)
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.list.set_valign(Gtk.Align.START); lsc.add(self.list)
        self.stack.add_titled(lsc, "liste", "Liste")

        # --- vue Mois (calendrier) ---
        cv = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.cal = Gtk.Calendar(); self.cal.set_valign(Gtk.Align.START)
        self.cal.connect("month-changed", lambda _c: self.remark())
        self.cal.connect("day-selected", lambda _c: self.show_day())
        self.cal.connect("day-selected-double-click", lambda _c: self.edit(None, self.sel_date()))
        cv.pack_start(self.cal, False, False, 0)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.daylbl = Gtk.Label(); self.daylbl.set_xalign(0); self.daylbl.get_style_context().add_class("day")
        right.pack_start(self.daylbl, False, False, 0)
        dsc = Gtk.ScrolledWindow(); dsc.set_vexpand(True)
        self.daylist = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.daylist.set_valign(Gtk.Align.START); dsc.add(self.daylist)
        right.pack_start(dsc, True, True, 0)
        cv.pack_start(right, True, True, 0)
        self.stack.add_titled(cv, "mois", "Mois")

        if "--view" in sys.argv:
            i = sys.argv.index("--view")
            if i + 1 < len(sys.argv):
                v = sys.argv[i + 1]
                GLib.idle_add(lambda: self.stack.set_visible_child_name(v))
        self._mtime = None
        self.refresh(); GLib.timeout_add(1200, self.poll)

    def sel_date(self):
        y, mo, da = self.cal.get_date(); return "%04d-%02d-%02d" % (y, mo + 1, da)

    def poll(self):
        try: m = os.path.getmtime(focus_applets.AGENDA_PATH)
        except OSError: m = 0
        if m != self._mtime: self.refresh()
        return True

    def refresh(self):
        try: self._mtime = os.path.getmtime(focus_applets.AGENDA_PATH)
        except OSError: self._mtime = 0
        self.fill_list(); self.remark(); self.show_day()

    def fill_list(self):
        for c in self.list.get_children(): self.list.remove(c)
        events = focus_applets.upcoming_events()
        if not events:
            e = Gtk.Label(label="Aucun rendez-vous à venir.\nCliquez « + Nouveau »."); e.set_xalign(0)
            e.get_style_context().add_class("empty"); e.set_line_wrap(True)
            self.list.pack_start(e, False, False, 0); self.list.show_all(); return
        cur = None
        for ev in events:
            if ev["date"] != cur:
                cur = ev["date"]
                d = Gtk.Label(label=focus_applets.fr_date(cur)); d.set_xalign(0)
                d.get_style_context().add_class("day"); self.list.pack_start(d, False, False, 0)
            self.list.pack_start(self.row(ev), False, False, 0)
        self.list.show_all()

    def remark(self):
        self.cal.clear_marks()
        y, mo, _ = self.cal.get_date()
        for e in focus_applets.load_events():
            try: d = datetime.date.fromisoformat(e["date"])
            except Exception: continue
            if d.year == y and d.month == mo + 1: self.cal.mark_day(d.day)

    def show_day(self):
        date = self.sel_date()
        self.daylbl.set_text(focus_applets.fr_date(date))
        for c in self.daylist.get_children(): self.daylist.remove(c)
        evs = [e for e in focus_applets.load_events() if e.get("date") == date]
        evs.sort(key=lambda e: e.get("time", ""))
        if not evs:
            e = Gtk.Label(label="Rien ce jour. Double-cliquez le jour pour ajouter.")
            e.get_style_context().add_class("empty"); e.set_xalign(0); e.set_line_wrap(True)
            self.daylist.pack_start(e, False, False, 0)
        else:
            for ev in evs: self.daylist.pack_start(self.row(ev), False, False, 0)
        self.daylist.show_all()

    def row(self, ev):
        b = Gtk.Button(); b.get_style_context().add_class("evt"); b.set_relief(Gtk.ReliefStyle.NONE)
        h = Gtk.Box(spacing=14)
        tm = Gtk.Label(label=ev.get("time", "")); tm.get_style_context().add_class("time")
        tm.set_valign(Gtk.Align.CENTER); h.pack_start(tm, False, False, 0)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        ti = Gtk.Label(label=ev["title"]); ti.set_xalign(0); ti.get_style_context().add_class("etitle")
        v.pack_start(ti, False, False, 0)
        if ev.get("note"):
            no = Gtk.Label(label=ev["note"]); no.set_xalign(0); no.set_ellipsize(3)
            no.get_style_context().add_class("enote"); v.pack_start(no, False, False, 0)
        h.pack_start(v, True, True, 0); b.add(h)
        b.connect("clicked", lambda _w: self.edit(ev["id"])); return b

    def edit(self, eid, date=None):
        cmd = ["python3", LIBDIR + "/event_dialog.py"]
        if eid is not None: cmd += ["--id", str(eid)]
        if date is not None: cmd += ["--date", date]
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, start_new_session=True)

pal = focus_theme.for_activity(focus_theme.focused_ws_name())
prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Agenda(); w.connect("destroy", Gtk.main_quit); w.show_all()
GLib.timeout_add(250, lambda: focus_theme.place_floating("focus-agenda", 820, 620) or False)
Gtk.main()
