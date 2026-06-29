#!/usr/bin/env python3
# Focus DE - dialogue flottant : creer / modifier / supprimer un rendez-vous.
# usage: event_dialog.py [--id <n>] [--date YYYY-MM-DD]
import gi, sys, datetime
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme, focus_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("focus-event-dialog")

def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv): return sys.argv[i + 1]
    return default

EID = arg("--id"); EID = int(EID) if EID is not None else None

CSS = """
window { background: @bg@; }
.title { font-size: 18px; font-weight: bold; color: @ink@; }
.lbl { color: @ink_soft@; font-size: 13px; }
entry, spinbutton { background: @surface@; color: @ink@; border-radius: 10px; border: 1px solid @border@; }
calendar { background: @surface@; color: @ink@; border-radius: 10px; border: 1px solid @border@; }
calendar:selected { background: @accent_strong@; color: @accent_ink@; }
.save { background: @accent_strong@; color: @accent_ink@; border-radius: 12px; padding: 8px 22px; font-weight: bold; }
.del  { background: @bg@; color: @ink_soft@; border-radius: 12px; padding: 8px 16px; border: 1px solid @border@; }
"""

class Dlg(Gtk.Window):
    def __init__(self):
        super().__init__(title="Rendez-vous")
        self.set_default_size(440, 560)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(16)
        self.add(box)
        t = Gtk.Label(label="Nouveau rendez-vous" if EID is None else "Modifier le rendez-vous")
        t.set_xalign(0); t.get_style_context().add_class("title")
        box.pack_start(t, False, False, 0)
        self.title = Gtk.Entry(); self.title.set_placeholder_text("Titre du rendez-vous…")
        box.pack_start(self.title, False, False, 0)
        self.cal = Gtk.Calendar(); box.pack_start(self.cal, False, False, 0)
        tl = Gtk.Box(spacing=8)
        tl.pack_start(self._lbl("Heure"), False, False, 0)
        self.hh = Gtk.SpinButton.new_with_range(0, 23, 1); self.hh.set_value(9)
        self.mm = Gtk.SpinButton.new_with_range(0, 59, 5); self.mm.set_value(0)
        for s in (self.hh, self.mm): s.set_orientation(Gtk.Orientation.VERTICAL)
        tl.pack_start(self.hh, False, False, 0); tl.pack_start(Gtk.Label(label=":"), False, False, 0)
        tl.pack_start(self.mm, False, False, 0)
        box.pack_start(tl, False, False, 0)
        box.pack_start(self._lbl("Note"), False, False, 0)
        self.note = Gtk.Entry(); self.note.set_placeholder_text("Détails (optionnel)…")
        box.pack_start(self.note, False, False, 0)
        bar = Gtk.Box(spacing=8)
        if EID is not None:
            d = Gtk.Button(label="Supprimer"); d.get_style_context().add_class("del")
            d.connect("clicked", self.delete); bar.pack_start(d, False, False, 0)
        c = Gtk.Button(label="Annuler"); c.get_style_context().add_class("del")
        c.connect("clicked", lambda _w: Gtk.main_quit()); bar.pack_end(c, False, False, 0)
        sv = Gtk.Button(label="Enregistrer"); sv.get_style_context().add_class("save")
        sv.connect("clicked", self.save); bar.pack_end(sv, False, False, 0)
        box.pack_start(bar, False, False, 0)
        # pre-remplissage
        date = arg("--date")
        if EID is not None:
            e = focus_applets.get_event(EID)
            if e:
                self.title.set_text(e["title"]); self.note.set_text(e.get("note", ""))
                date = e["date"]
                try:
                    h, m = e.get("time", "09:00").split(":")
                    self.hh.set_value(int(h)); self.mm.set_value(int(m))
                except Exception: pass
        try:
            d = datetime.date.fromisoformat(date) if date else datetime.date.today()
        except Exception:
            d = datetime.date.today()
        self.cal.select_month(d.month - 1, d.year); self.cal.select_day(d.day)
        self.connect("key-press-event", lambda _w, ev: Gtk.main_quit() if ev.keyval == Gdk.KEY_Escape else None)

    def _lbl(self, s):
        l = Gtk.Label(label=s); l.set_xalign(0); l.get_style_context().add_class("lbl"); return l

    def save(self, _w):
        y, mo, da = self.cal.get_date()  # mois 0-based
        date = "%04d-%02d-%02d" % (y, mo + 1, da)
        tm = "%02d:%02d" % (int(self.hh.get_value()), int(self.mm.get_value()))
        title = self.title.get_text().strip() or "Rendez-vous"
        focus_applets.upsert_event(EID, date, tm, title, self.note.get_text().strip())
        Gtk.main_quit()

    def delete(self, _w):
        focus_applets.delete_event(EID); Gtk.main_quit()

pal = focus_theme.for_activity(focus_theme.focused_ws_name())
prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Dlg(); w.connect("destroy", Gtk.main_quit); w.show_all()
GLib.timeout_add(250, lambda: focus_theme.place_floating("focus-event-dialog", 440, 560) or False)
Gtk.main()
