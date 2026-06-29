#!/usr/bin/env python3
# Onyx / Focus DE - applet Notes (widget embarquable). Notes contextuelles a l'activite ;
# scope "__global__" depuis l'accueil. oeil = voir/editer, croix = supprimer, + Nouvelle.
import gi, os, subprocess, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
LIBDIR = os.path.dirname(os.path.realpath(__file__))
import onyx_theme, onyx_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import os; HOME = os.path.expanduser("~")

EXPAND = True
CSS = """
.notes-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 10px; }
.notes-head { font-size: 16px; font-weight: bold; color: @ink@; }
.notes-scope { font-size: 11px; color: @ink_soft@; }
.notes-new { background: @accent@; color: @accent_ink@; border-radius: 10px; padding: 4px 10px; }
.notes-new:hover { background: @accent_strong@; }
.notes-title { font-size: 14px; color: @ink@; }
.notes-empty { color: @ink_soft@; font-size: 13px; }
.notes-card row, .notes-card list { background: transparent; }
"""

class NotesWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.scope = (ctx or {}).get("scope") or onyx_applets.notes_scope(onyx_theme.focused_ws_name())
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("notes-card")
        self.pack_start(card, True, True, 0)
        head = Gtk.Box(spacing=6)
        tt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        h = Gtk.Label(label="Notes"); h.set_xalign(0); h.get_style_context().add_class("notes-head")
        sc = Gtk.Label(label=onyx_applets.scope_label(self.scope)); sc.set_xalign(0)
        sc.get_style_context().add_class("notes-scope")
        tt.pack_start(h, False, False, 0); tt.pack_start(sc, False, False, 0)
        head.pack_start(tt, True, True, 0)
        nb = Gtk.Button(label="+ Nouvelle"); nb.get_style_context().add_class("notes-new")
        nb.connect("clicked", lambda _w: self.open_note(None))
        head.pack_end(nb, False, False, 0)
        card.pack_start(head, False, False, 0)
        win = Gtk.ScrolledWindow(); win.set_propagate_natural_height(True)
        win.set_min_content_height(60); win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.lb = Gtk.ListBox(); self.lb.set_selection_mode(Gtk.SelectionMode.NONE)
        win.add(self.lb); card.pack_start(win, True, True, 0)
        self._mtime = None
        self.refresh(); GLib.timeout_add(1200, self.poll)

    def poll(self):
        try: m = os.path.getmtime(onyx_applets.notes_path(self.scope))
        except OSError: m = 0
        if m != self._mtime: self.refresh()
        return True

    def refresh(self):
        try: self._mtime = os.path.getmtime(onyx_applets.notes_path(self.scope))
        except OSError: self._mtime = 0
        for r in self.lb.get_children(): self.lb.remove(r)
        notes = onyx_applets.load_notes(self.scope)
        if not notes:
            e = Gtk.Label(label="Aucune note.\nCliquez « + Nouvelle »."); e.set_xalign(0)
            e.get_style_context().add_class("notes-empty"); e.set_line_wrap(True); e.set_margin_top(8)
            self.lb.add(e); self.lb.show_all(); return
        for n in notes:
            row = Gtk.Box(spacing=4); row.set_margin_top(3); row.set_margin_bottom(3)
            lbl = Gtk.Label(label=n["title"]); lbl.set_xalign(0); lbl.set_ellipsize(3)
            lbl.get_style_context().add_class("notes-title")
            row.pack_start(lbl, True, True, 0)
            row.pack_end(self.icon("user-trash-symbolic", self.del_note, n["id"]), False, False, 0)
            row.pack_end(self.icon("view-reveal-symbolic", self.open_note, n["id"]), False, False, 0)
            self.lb.add(row)
        self.lb.show_all()

    def icon(self, name, cb, arg):
        b = Gtk.Button(); b.set_image(Gtk.Image.new_from_icon_name(name, Gtk.IconSize.BUTTON))
        b.set_relief(Gtk.ReliefStyle.NONE); b.connect("clicked", lambda _w: cb(arg)); return b

    def open_note(self, nid):
        cmd = ["python3", LIBDIR + "/note_dialog.py", "--scope", self.scope]
        if nid is not None: cmd += ["--id", str(nid)]
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, start_new_session=True)

    def del_note(self, nid):
        onyx_applets.delete_note(self.scope, nid); self.refresh()

def make(ctx=None): return NotesWidget(ctx)

if __name__ == "__main__":
    GLib.set_prgname("onyx-applet-notes")
    pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
