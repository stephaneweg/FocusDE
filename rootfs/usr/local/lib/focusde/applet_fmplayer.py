#!/usr/bin/env python3
# Focus DE - applet FM-Player : joue des morceaux FM-Song (.fms) via le moteur de
# fmtracker (fluidsynth). Lit un fichier seul OU un dossier entier (liste de lecture).
import gi, os, sys
LIBDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIBDIR)
sys.path.insert(0, os.path.join(LIBDIR, "apps"))   # the fmtracker engine package
import onyx_theme
from fmtracker import fms as fmsmod, synth as synthmod, sequencer as seqmod
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

HOME = os.path.expanduser("~")
EXPAND = True

CSS = """
.fmp-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 10px; }
.fmp-head { font-size: 16px; font-weight: bold; color: @ink@; }
.fmp-now { font-size: 13px; color: @ink@; }
.fmp-empty { font-size: 13px; color: @ink_soft@; }
.fmp-src button { background: @bg@; border-radius: 10px; border: 1px solid @border@; padding: 2px 8px; font-size: 12px; }
.fmp-src button:hover { background: @accent@; }
.fmp-ctrl button { background: @bg@; border-radius: 12px; border: 1px solid @border@; margin: 3px; padding: 6px; }
.fmp-ctrl button:hover { background: @accent@; }
.fmp-ctrl button.play { background: @accent_strong@; }
.fmp-card list, .fmp-card row { background: transparent; }
.fmp-card row:selected, .fmp-card row:selected .fmp-track { background: @accent@; color: @accent_ink@; border-radius: 8px; }
.fmp-track { font-size: 13px; color: @ink@; }
"""


def default_dir():
    for d in (os.path.join(HOME, "fms"), os.path.join(HOME, "Music")):
        try:
            if any(f.lower().endswith(".fms") for f in os.listdir(d)):
                return d
        except OSError:
            pass
    return os.path.join(HOME, "fms")


def _title(path):
    return os.path.splitext(os.path.basename(path))[0]


class FmPlayerWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.synth = synthmod.Synth()
        self.seq = seqmod.Sequencer(self.synth)
        self.seq.loop = False                 # a player lets songs end (then auto-next)
        self.tracks = []
        self.idx = -1
        self.user_paused = False
        self.stopped = True

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("fmp-card")
        self.pack_start(card, True, True, 0)

        head = Gtk.Box(spacing=6)
        hl = Gtk.Label(label="FM-Player"); hl.set_xalign(0)
        hl.get_style_context().add_class("fmp-head")
        head.pack_start(hl, True, True, 0)
        src = Gtk.Box(spacing=4); src.get_style_context().add_class("fmp-src")
        bf = Gtk.Button(label="Fichier"); bf.connect("clicked", self.choose_file)
        bd = Gtk.Button(label="Dossier"); bd.connect("clicked", self.choose_folder)
        src.pack_start(bf, False, False, 0); src.pack_start(bd, False, False, 0)
        head.pack_end(src, False, False, 0)
        card.pack_start(head, False, False, 0)

        self.now = Gtk.Label(label="—"); self.now.set_xalign(0); self.now.set_ellipsize(3)
        self.now.get_style_context().add_class("fmp-now")
        card.pack_start(self.now, False, False, 0)

        ctrl = Gtk.Box(spacing=2); ctrl.get_style_context().add_class("fmp-ctrl")
        ctrl.set_halign(Gtk.Align.CENTER)
        self.bp = self._btn("media-skip-backward-symbolic", lambda _w: self.skip(-1))
        self.bplay = self._btn("media-playback-start-symbolic", self.toggle)
        self.bplay.get_style_context().add_class("play")
        self.bs = self._btn("media-playback-stop-symbolic", self.stop)
        self.bn = self._btn("media-skip-forward-symbolic", lambda _w: self.skip(1))
        for b in (self.bp, self.bplay, self.bs, self.bn):
            ctrl.pack_start(b, False, False, 0)
        card.pack_start(ctrl, False, False, 0)

        sw = Gtk.ScrolledWindow(); sw.set_propagate_natural_height(True)
        sw.set_min_content_height(60)
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.lb = Gtk.ListBox()
        self.lb.connect("row-activated", lambda _l, r: self.play(r.get_index()))
        sw.add(self.lb); card.pack_start(sw, True, True, 0)

        self.load_dir(default_dir())
        self.connect("destroy", self._cleanup)
        GLib.timeout_add_seconds(1, self._poll_end)

    # -- widgets -------------------------------------------------------------

    def _btn(self, icon, cb):
        b = Gtk.Button()
        b.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR))
        b.set_relief(Gtk.ReliefStyle.NONE); b.connect("clicked", cb)
        return b

    def _icon(self, name):
        self.bplay.set_image(Gtk.Image.new_from_icon_name(name, Gtk.IconSize.LARGE_TOOLBAR))
        self.bplay.show_all()

    def _fill(self):
        for c in self.lb.get_children():
            self.lb.remove(c)
        if not self.tracks:
            e = Gtk.Label(label="Aucun morceau .fms.\n« Fichier » ou « Dossier » pour en charger.")
            e.get_style_context().add_class("fmp-empty"); e.set_xalign(0); e.set_line_wrap(True)
            self.lb.add(e)
        else:
            for t in self.tracks:
                lab = Gtk.Label(label=_title(t)); lab.set_xalign(0); lab.set_ellipsize(3)
                lab.get_style_context().add_class("fmp-track")
                lab.set_margin_top(3); lab.set_margin_bottom(3)
                self.lb.add(lab)
        self.lb.show_all()

    # -- sources -------------------------------------------------------------

    def load_dir(self, d):
        try:
            self.tracks = sorted(os.path.join(d, f) for f in os.listdir(d)
                                 if f.lower().endswith(".fms"))
        except OSError:
            self.tracks = []
        self.idx = -1; self._fill()

    def load_file(self, path):
        self.tracks = [path]; self.idx = -1; self._fill()

    def choose_file(self, _w):
        dlg = Gtk.FileChooserDialog(title="Ouvrir un morceau (.fms)",
                                    transient_for=self.get_toplevel(),
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("Annuler", Gtk.ResponseType.CANCEL, "Ouvrir", Gtk.ResponseType.ACCEPT)
        flt = Gtk.FileFilter(); flt.set_name("FM-Song (.fms)")
        flt.add_pattern("*.fms"); flt.add_pattern("*.FMS"); dlg.add_filter(flt)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            self.load_file(dlg.get_filename()); self.play(0)
        dlg.destroy()

    def choose_folder(self, _w):
        dlg = Gtk.FileChooserDialog(title="Choisir un dossier de morceaux",
                                    transient_for=self.get_toplevel(),
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons("Annuler", Gtk.ResponseType.CANCEL, "Ouvrir", Gtk.ResponseType.ACCEPT)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            self.load_dir(dlg.get_filename())
        dlg.destroy()

    # -- transport -----------------------------------------------------------

    def play(self, idx):
        if not (0 <= idx < len(self.tracks)):
            return
        try:
            song = fmsmod.load_fms(self.tracks[idx])
        except Exception as e:                 # noqa: BLE001
            self.now.set_text("Erreur : %s" % e)
            return
        self.idx = idx
        self.stopped = False
        self.user_paused = False
        self.seq.play(song)
        self.now.set_text(_title(self.tracks[idx]))
        row = self.lb.get_row_at_index(idx)
        if row:
            self.lb.select_row(row)
        self._icon("media-playback-pause-symbolic")

    def toggle(self, *_):
        if self.idx < 0:
            if self.tracks:
                self.play(0)
            return
        if self.user_paused:
            self.seq.resume(); self.user_paused = False
            self._icon("media-playback-pause-symbolic")
        elif self.seq.playing and not self.seq.paused:
            self.seq.pause(); self.user_paused = True
            self._icon("media-playback-start-symbolic")
        else:                                   # finished or stopped -> replay
            self.play(self.idx)

    def stop(self, *_):
        self.seq.stop(); self.stopped = True; self.user_paused = False
        self.now.set_text("—"); self._icon("media-playback-start-symbolic")

    def skip(self, d):
        if self.tracks:
            self.play((self.idx + d) % len(self.tracks))

    def _poll_end(self):
        # auto-advance to the next track when the current one finishes
        if (self.idx >= 0 and not self.stopped and not self.user_paused
                and not self.seq.playing):
            self.skip(1)
        return True

    def _cleanup(self, _w):
        try:
            self.seq.stop(); self.synth.shutdown()
        except Exception:                       # noqa: BLE001
            pass


def make(ctx=None):
    return FmPlayerWidget(ctx)


if __name__ == "__main__":
    GLib.set_prgname("onyx-applet-fmplayer")
    pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
    prov = Gtk.CssProvider()
    prov.load_from_data(onyx_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit)
    w.show_all(); Gtk.main()
