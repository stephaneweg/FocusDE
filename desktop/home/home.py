#!/usr/bin/env python3
# Onyx - accueil (design facon mockup) : en-tete + cartes + grandes tuiles d'activites.
import gi, subprocess, json, os, time, datetime, getpass, sys
sys.path.insert(0, "/home/maison")
import onyx_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
GLib.set_prgname("onyx-home")

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
TILE_COLORS = ["#7C6FE0", "#C2497E", "#B7791F", "#3AA76D", "#3457A8", "#D4537E"]
HUBS = [("Travailler", "#3F51B5"), ("Apprendre", "#1D9E75"), ("Jouer", "#2E9E5B"),
        ("Naviguer", "#2F86C9"), ("Créer", "#D85A30")]
HUBNAMES = {h[0] for h in HUBS}

CSS = """
window { background: @bg@; }
.greet { font-size: 24px; font-weight: bold; color: @ink@; }
.date  { font-size: 14px; color: @ink_soft@; }
.avatar { background: @avatar@; border-radius: 22px; }
.clock { font-size: 18px; font-weight: bold; color: @ink@; }
.infocard { background: @surface@; border-radius: 16px; padding: 16px 18px; margin: 4px; }
.infolabel { font-size: 13px; color: @ink_soft@; }
.infomain  { font-size: 18px; font-weight: bold; color: @ink@; }
.infosub   { font-size: 13px; color: @ink_soft@; }
.tile { border-radius: 18px; margin: 8px; }
.tilename { font-size: 17px; font-weight: bold; color: #FFFFFF; }
.tileicon { background: rgba(255,255,255,0.22); border-radius: 10px; }
.newtile { background: transparent; border: 2px dashed @accent_strong@; border-radius: 18px; margin: 8px; }
.newtile label { color: @ink_soft@; font-size: 15px; }
"""

def sway(*a): subprocess.run(["swaymsg", "-q"] + list(a))
def style(w, css):
    p = Gtk.CssProvider(); p.load_from_data(css.encode())
    w.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)

def list_activities():
    try: ws = json.loads(subprocess.check_output(["swaymsg", "-t", "get_workspaces"]))
    except Exception: return []
    return [w["name"] for w in ws
            if w["name"] != "Accueil" and not w["name"][:1].isdigit()
            and not w["name"].endswith("old") and w["name"] not in HUBNAMES]

def profile_name():
    try:
        n = open(os.path.expanduser("~/.config/onyx/name")).read().strip()
        if n: return n
    except Exception:
        pass
    return getpass.getuser()

class Home(Gtk.Window):
    def __init__(self):
        super().__init__(title="Accueil")
        sc = Gtk.ScrolledWindow(); self.add(sc)
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for m in ("top", "start", "end", "bottom"):
            getattr(self.root, "set_margin_" + m)(26)
        sc.add(self.root)
        self.build(); GLib.timeout_add_seconds(2, self.refresh)

    def build(self):
        for c in self.root.get_children(): self.root.remove(c)
        self.root.pack_start(self.header(), False, False, 0)
        self.root.pack_start(self.cards(), False, False, 0)
        flow = Gtk.FlowBox(); flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(2); flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        for hname, hcolor in HUBS: flow.add(self.hub_tile(hname, hcolor))
        acts = list_activities()
        for i, n in enumerate(acts): flow.add(self.tile(n, TILE_COLORS[i % len(TILE_COLORS)]))
        flow.add(self.newtile())
        self.root.pack_start(flow, True, True, 0)
        self.show_all()

    def header(self):
        h = Gtk.Box(spacing=12)
        av = Gtk.Box(); av.get_style_context().add_class("avatar")
        av.set_size_request(44, 44)
        il = Gtk.Label(label=profile_name()[:1].upper()); il.set_markup(
            '<span foreground="white" font="18" weight="bold">%s</span>' % profile_name()[:1].upper())
        av.set_center_widget(il)
        h.pack_start(av, False, False, 0)
        vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        g = Gtk.Label(label="Bonjour, " + profile_name()); g.set_xalign(0); g.get_style_context().add_class("greet")
        d = datetime.date.today()
        dl = Gtk.Label(label="%s %d %s" % (JOURS[d.weekday()], d.day, MOIS[d.month-1]))
        dl.set_xalign(0); dl.get_style_context().add_class("date")
        vb.pack_start(g, False, False, 0); vb.pack_start(dl, False, False, 0)
        h.pack_start(vb, False, False, 0)
        h.pack_start(Gtk.Box(), True, True, 0)  # spacer
        self.clock = Gtk.Label(); self.clock.get_style_context().add_class("clock")
        h.pack_end(self.clock, False, False, 10)
        return h

    def cards(self):
        row = Gtk.Box(spacing=8, homogeneous=True)
        acts = list_activities()
        last = acts[0] if acts else "—"
        row.pack_start(self.infocard("Reprendre", last, "dernière activité"), True, True, 0)
        row.pack_start(self.infocard("En ce moment", "—", "rien en lecture"), True, True, 0)
        row.pack_start(self.infocard("Aujourd'hui", "%d activités" % len(acts), ""), True, True, 0)
        return row

    def infocard(self, label, main, sub):
        c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c.get_style_context().add_class("infocard")
        l = Gtk.Label(label=label); l.set_xalign(0); l.get_style_context().add_class("infolabel")
        m = Gtk.Label(label=main); m.set_xalign(0); m.get_style_context().add_class("infomain")
        c.pack_start(l, False, False, 0); c.pack_start(m, False, False, 0)
        if sub:
            s = Gtk.Label(label=sub); s.set_xalign(0); s.get_style_context().add_class("infosub")
            c.pack_start(s, False, False, 0)
        return c

    def tile(self, name, color):
        b = Gtk.Button(); b.get_style_context().add_class("tile")
        b.set_size_request(210, 200)
        style(b, "button.tile { background:%s; } button.tile:hover { background:%s; }" % (color, color))
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        v.set_margin_top(16); v.set_margin_start(16); v.set_margin_end(16); v.set_margin_bottom(16)
        ic = Gtk.Box(); ic.get_style_context().add_class("tileicon"); ic.set_size_request(34, 34)
        ic.set_halign(Gtk.Align.START)
        v.pack_start(ic, False, False, 0)
        v.pack_start(Gtk.Box(), True, True, 0)
        nm = Gtk.Label(label=name); nm.set_xalign(0); nm.set_line_wrap(True)
        nm.get_style_context().add_class("tilename")
        v.pack_start(nm, False, False, 0)
        b.add(v)
        b.connect("clicked", lambda _w, n=name: sway("workspace", n))
        return b

    def hub_tile(self, name, color):
        b = Gtk.Button(); b.get_style_context().add_class("tile")
        b.set_size_request(210, 200)
        style(b, "button.tile { background:%s; } button.tile:hover { background:%s; }" % (color, color))
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        v.set_margin_top(16); v.set_margin_start(16); v.set_margin_end(16); v.set_margin_bottom(16)
        ic = Gtk.Box(); ic.get_style_context().add_class("tileicon"); ic.set_size_request(34, 34)
        ic.set_halign(Gtk.Align.START)
        v.pack_start(ic, False, False, 0)
        v.pack_start(Gtk.Box(), True, True, 0)
        nm = Gtk.Label(label=name); nm.set_xalign(0); nm.set_line_wrap(True)
        nm.get_style_context().add_class("tilename")
        v.pack_start(nm, False, False, 0)
        b.add(v)
        b.connect("clicked", lambda _w, n=name:
                  subprocess.Popen(["python3", "/home/maison/activity.py", "hub", n]))
        return b

    def newtile(self):
        b = Gtk.Button(); b.get_style_context().add_class("newtile"); b.set_size_request(210, 200)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        v.set_valign(Gtk.Align.CENTER)
        p = Gtk.Label(); p.set_markup('<span foreground="#6A6680" font="30">+</span>')
        l = Gtk.Label(label="Nouvelle activité")
        v.pack_start(p, False, False, 0); v.pack_start(l, False, False, 0)
        b.add(v); b.connect("clicked", self.new_activity)
        return b

    def new_activity(self, _w):
        d = Gtk.Dialog(title="Nouvelle activité", transient_for=self, modal=True)
        d.add_button("Annuler", Gtk.ResponseType.CANCEL); d.add_button("Créer", Gtk.ResponseType.OK)
        d.set_default_response(Gtk.ResponseType.OK)
        e = Gtk.Entry(); e.set_placeholder_text("Nom de l'activité"); e.set_activates_default(True)
        ca = d.get_content_area()
        for m in ("top", "bottom", "start", "end"): getattr(ca, "set_margin_" + m)(12)
        ca.pack_start(e, True, True, 0); d.show_all()
        if d.run() == Gtk.ResponseType.OK:
            name = e.get_text().strip() or "Activité"
            subprocess.Popen(["python3", "/home/maison/activity.py", "new", "--auto", name])
        d.destroy()

    def parents(self, _w):
        d = Gtk.MessageDialog(transient_for=self, modal=True, buttons=Gtk.ButtonsType.OK,
                              text="Espace parents")
        d.format_secondary_text("Réglages et contrôle parental — à venir.")
        d.run(); d.destroy()

    def refresh(self):
        self.clock.set_text(time.strftime("%H:%M")); self.build(); return True

prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css(CSS))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
w = Home(); w.connect("destroy", Gtk.main_quit); w.show_all()
w.clock.set_text(time.strftime("%H:%M"))
Gtk.main()
