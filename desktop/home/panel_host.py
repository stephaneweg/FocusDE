#!/usr/bin/env python3
# Onyx / Focus DE - hote du panneau gauche : UNE fenetre qui empile les applets choisis
# comme des widgets GTK (hauteur naturelle adaptative, pas de bordure, un seul scroll).
import gi, importlib, subprocess, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import onyx_theme, onyx_applets
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-panel")
import os; HOME = os.path.expanduser("~")

BASE_CSS = """
window { background: @bg@; }
scrolledwindow, viewport { background: @bg@; border: none; }
.panel-head { font-size: 12px; color: @ink_soft@; padding: 0 4px; }
.panel-add { background: @accent@; color: @accent_ink@; border-radius: 10px; padding: 2px 12px;
             font-size: 16px; font-weight: bold; }
.panel-add:hover { background: @accent_strong@; }
.panel-empty { color: @ink_soft@; font-size: 13px; padding: 6px 4px; }
"""

def main():
    wsname = onyx_theme.focused_ws_name()
    scope = onyx_applets.notes_scope(wsname)
    ids = onyx_applets.load_applet_sel(wsname)
    if not ids:
        ids = list(onyx_applets.DEFAULT_HOME) if (wsname or "") == "Accueil" else []
    ctx = {"wsname": wsname, "scope": scope}

    mods, css = [], BASE_CSS
    for aid in ids:
        a = onyx_applets.by_id(aid)
        if not a: continue
        try:
            m = importlib.import_module(a["module"])
            mods.append((a, m)); css += "\n" + getattr(m, "CSS", "")
        except Exception as e:
            sys.stderr.write("applet %s: %s\n" % (aid, e))

    pal = onyx_theme.for_activity(wsname)
    prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(css, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    win = Gtk.Window(title="Panneau")
    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    for m in ("top", "start", "end", "bottom"): getattr(root, "set_margin_" + m)(8)
    win.add(root)
    # en-tete FIXE : titre + bouton "+" (toujours visible, hors du defilement)
    head = Gtk.Box(spacing=6)
    hl = Gtk.Label(label="Applets"); hl.set_xalign(0); hl.get_style_context().add_class("panel-head")
    head.pack_start(hl, True, True, 0)
    addb = Gtk.Button(label="+"); addb.get_style_context().add_class("panel-add")
    addb.set_tooltip_text("Ajouter / retirer des applets")
    addb.connect("clicked", lambda _w: subprocess.Popen(
        ["python3", HOME + "/applet_mgr.py"], stdin=subprocess.DEVNULL, start_new_session=True))
    head.pack_end(addb, False, False, 0)
    root.pack_start(head, False, False, 0)
    # zone defilante : les applets s'empilent a leur hauteur naturelle ; scroll si ca deborde
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_propagate_natural_width(True)
    root.pack_start(scroller, True, True, 0)
    stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    stack.set_valign(Gtk.Align.START)
    scroller.add(stack)
    if not mods:
        e = Gtk.Label(label="Aucun applet.\nTouchez « + » pour en ajouter.")
        e.set_xalign(0); e.set_line_wrap(True); e.get_style_context().add_class("panel-empty")
        stack.pack_start(e, False, False, 0)
    for a, m in mods:
        try:
            w = m.make(ctx)
        except Exception as ex:
            sys.stderr.write("make %s: %s\n" % (a["id"], ex)); continue
        stack.pack_start(w, False, False, 0)   # hauteur naturelle ; le scroll parent gere le debordement
    win.connect("destroy", Gtk.main_quit); win.show_all(); Gtk.main()

main()
