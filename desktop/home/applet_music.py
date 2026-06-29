#!/usr/bin/env python3
# Onyx / Focus DE - applet Musique (widget embarquable, lecteur GStreamer, lit ~/Music).
import gi, os, sys
sys.path.insert(0, "/home/maison")
import onyx_theme
gi.require_version("Gtk", "3.0"); gi.require_version("Gst", "1.0")
from gi.repository import Gtk, GLib, Gdk, Gst
Gst.init(None)
MUSIC = os.path.expanduser("~/Music")
EXTS = (".mp3", ".ogg", ".flac", ".wav", ".m4a", ".opus", ".aac")

EXPAND = True
CSS = """
.music-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 10px; }
.music-head { font-size: 16px; font-weight: bold; color: @ink@; }
.music-track { font-size: 13px; color: @ink@; }
.music-empty { font-size: 13px; color: @ink_soft@; }
.music-ctrl button { background: @bg@; border-radius: 12px; border: 1px solid @border@; margin: 3px; padding: 6px; }
.music-ctrl button:hover { background: @accent@; }
.music-ctrl button.play { background: @accent_strong@; }
.music-card list, .music-card row { background: transparent; }
.music-card row:selected, .music-card row:selected .music-track { background: @accent@; color: @accent_ink@; border-radius: 8px; }
"""

class MusicWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.tracks = sorted(os.path.join(MUSIC, f) for f in os.listdir(MUSIC)
                             if f.lower().endswith(EXTS)) if os.path.isdir(MUSIC) else []
        self.idx = -1; self.playing = False
        self.player = Gst.ElementFactory.make("playbin", "player")
        bus = self.player.get_bus(); bus.add_signal_watch()
        bus.connect("message::eos", lambda *_: self.skip(1))
        bus.connect("message::error", self.on_err)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("music-card"); self.pack_start(card, True, True, 0)
        h = Gtk.Label(label="Musique"); h.set_xalign(0); h.get_style_context().add_class("music-head")
        card.pack_start(h, False, False, 0)
        self.now = Gtk.Label(label="—"); self.now.set_xalign(0); self.now.set_ellipsize(3)
        self.now.get_style_context().add_class("music-track"); card.pack_start(self.now, False, False, 0)
        ctrl = Gtk.Box(spacing=2); ctrl.get_style_context().add_class("music-ctrl")
        ctrl.set_halign(Gtk.Align.CENTER)
        self.bp = self.btn("media-skip-backward-symbolic", lambda _w: self.skip(-1))
        self.bplay = self.btn("media-playback-start-symbolic", lambda _w: self.toggle())
        self.bplay.get_style_context().add_class("play")
        self.bn = self.btn("media-skip-forward-symbolic", lambda _w: self.skip(1))
        for b in (self.bp, self.bplay, self.bn): ctrl.pack_start(b, False, False, 0)
        card.pack_start(ctrl, False, False, 0)
        win = Gtk.ScrolledWindow(); win.set_propagate_natural_height(True)
        win.set_min_content_height(60); win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.lb = Gtk.ListBox()
        self.lb.connect("row-activated", lambda _l, r: self.play(r.get_index()))
        win.add(self.lb); card.pack_start(win, True, True, 0)
        if not self.tracks:
            e = Gtk.Label(label="Aucune musique.\nDéposez des fichiers dans ~/Music.")
            e.get_style_context().add_class("music-empty"); e.set_xalign(0); e.set_line_wrap(True)
            self.lb.add(e)
        else:
            for t in self.tracks:
                lab = Gtk.Label(label=os.path.splitext(os.path.basename(t))[0])
                lab.set_xalign(0); lab.set_ellipsize(3); lab.get_style_context().add_class("music-track")
                lab.set_margin_top(3); lab.set_margin_bottom(3); self.lb.add(lab)
        self.connect("destroy", lambda _w: self.player.set_state(Gst.State.NULL))

    def btn(self, icon, cb):
        b = Gtk.Button(); b.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR))
        b.set_relief(Gtk.ReliefStyle.NONE); b.connect("clicked", cb); return b

    def _seticon(self, name):
        self.bplay.set_image(Gtk.Image.new_from_icon_name(name, Gtk.IconSize.LARGE_TOOLBAR)); self.bplay.show_all()

    def play(self, idx):
        if not (0 <= idx < len(self.tracks)): return
        self.idx = idx; self.player.set_state(Gst.State.NULL)
        self.player.set_property("uri", Gst.filename_to_uri(self.tracks[idx]))
        self.player.set_state(Gst.State.PLAYING); self.playing = True
        self.now.set_text(os.path.splitext(os.path.basename(self.tracks[idx]))[0])
        self.lb.select_row(self.lb.get_row_at_index(idx)); self._seticon("media-playback-pause-symbolic")

    def toggle(self):
        if self.idx < 0: self.play(0); return
        if self.playing:
            self.player.set_state(Gst.State.PAUSED); self.playing = False
            self._seticon("media-playback-start-symbolic")
        else:
            self.player.set_state(Gst.State.PLAYING); self.playing = True
            self._seticon("media-playback-pause-symbolic")

    def skip(self, d):
        if self.tracks: self.play((self.idx + d) % len(self.tracks))

    def on_err(self, _bus, msg):
        err, _ = msg.parse_error(); self.now.set_text("Erreur: %s" % err.message)

def make(ctx=None): return MusicWidget(ctx)

if __name__ == "__main__":
    GLib.set_prgname("onyx-applet-music")
    pal = onyx_theme.for_activity(onyx_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(onyx_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
