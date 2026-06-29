#!/usr/bin/env python3
# Onyx / Focus DE - dialogue flottant pour creer/voir/editer une note.
# usage: note_dialog.py --scope <scope> [--id <n>]
import gi, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import onyx_theme, onyx_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-note-dialog")

def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv): return sys.argv[i + 1]
    return default

SCOPE = arg("--scope", "__global__")
NID = arg("--id"); NID = int(NID) if NID is not None else None

CSS = """
window { background: @bg@; }
.title { font-size: 18px; font-weight: bold; color: @ink@; }
entry { background: @surface@; color: @ink@; border-radius: 10px; border: 1px solid @border@; padding: 8px; }
textview, textview text { background: @surface@; color: @ink@; border-radius: 10px; font-size: 15px; }
.frame { border: 1px solid @border@; border-radius: 10px; }
.save { background: @accent_strong@; color: @accent_ink@; border-radius: 12px; padding: 8px 22px; font-weight: bold; }
.del  { background: @bg@; color: @ink_soft@; border-radius: 12px; padding: 8px 16px; border: 1px solid @border@; }
"""

class Dlg(Gtk.Window):
    def __init__(self):
        super().__init__(title="Note")
        self.set_default_size(520, 540)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("top", "start", "end", "bottom"): getattr(box, "set_margin_" + m)(16)
        self.add(box)
        head = Gtk.Box(spacing=8)
        t = Gtk.Label(label="Nouvelle note" if NID is None else "Note"); t.set_xalign(0)
        t.get_style_context().add_class("title")
        head.pack_start(t, True, True, 0)
        sub = Gtk.Label(label="· " + onyx_applets.scope_label(SCOPE))
        sub.get_style_context().add_class("title"); sub.set_opacity(0.45)
        head.pack_end(sub, False, False, 0)
        box.pack_start(head, False, False, 0)
        self.title = Gtk.Entry(); self.title.set_placeholder_text("Titre…")
        box.pack_start(self.title, False, False, 0)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.get_style_context().add_class("frame")
        self.body = Gtk.TextView(); self.body.set_wrap_mode(Gtk.WrapMode.WORD)
        self.body.set_left_margin(8); self.body.set_right_margin(8); self.body.set_top_margin(8)
        sc.add(self.body); box.pack_start(sc, True, True, 0)
        bar = Gtk.Box(spacing=8)
        if NID is not None:
            d = Gtk.Button(label="Supprimer"); d.get_style_context().add_class("del")
            d.connect("clicked", self.delete); bar.pack_start(d, False, False, 0)
        cancel = Gtk.Button(label="Annuler"); cancel.get_style_context().add_class("del")
        cancel.connect("clicked", lambda _w: Gtk.main_quit()); bar.pack_end(cancel, False, False, 0)
        save = Gtk.Button(label="Enregistrer"); save.get_style_context().add_class("save")
        save.connect("clicked", self.save); bar.pack_end(save, False, False, 0)
        box.pack_start(bar, False, False, 0)
        if NID is not None:
            n = onyx_applets.get_note(SCOPE, NID)
            if n: self.title.set_text(n["title"]); self.body.get_buffer().set_text(n["body"])
        self.connect("key-press-event", self._key)

    def _key(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape: Gtk.main_quit()

    def _body_text(self):
        b = self.body.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), True)

    def save(self, _w):
        title = self.title.get_text().strip() or "Sans titre"
        onyx_applets.upsert_note(SCOPE, NID, title, self._body_text())
        Gtk.main_quit()

    def delete(self, _w):
        onyx_applets.delete_note(SCOPE, NID)
        Gtk.main_quit()

pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(CSS, pal))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Dlg(); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
