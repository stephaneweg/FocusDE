"""GTK4 application: window, toolbar, keyboard/mouse wiring."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import GLib, Gdk, Gtk      # noqa: E402

from . import fms, gm                          # noqa: E402
from .gridview import GridView                 # noqa: E402
from .model import REST, Song, make_midi, midi_to_name   # noqa: E402
from .sequencer import Sequencer               # noqa: E402
from .synth import Synth                       # noqa: E402

APP_ID = "com.focusde.fmtracker"

# Letter -> semitone within an octave.
NOTE_KEYS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


class FmTrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="FM-Song Tracker")
        self.set_default_size(900, 640)

        self.synth = Synth()
        self.seq = Sequencer(self.synth)
        self.seq.on_row = self._on_row_threadsafe
        self.song = Song.new_default()
        self.edit_octave = 4
        self._sync_guard = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)
        root.append(self._build_toolbar())

        self.grid = GridView(on_cell_clicked=self._on_cell_clicked)
        self.grid.set_song(self.song)
        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(self.grid)
        root.append(scroller)

        self.status = Gtk.Label(xalign=0)
        self.status.set_margin_start(8)
        self.status.set_margin_top(2)
        self.status.set_margin_bottom(4)
        root.append(self.status)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)

        self.connect("close-request", self._on_close)
        self._refresh_patterns()
        self._sync_instrument()
        self._update_status()

    # -- UI construction -----------------------------------------------------

    def _build_toolbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for m in ("start", "end", "top", "bottom"):
            getattr(bar, f"set_margin_{m}")(6)

        def button(label, cb):
            b = Gtk.Button(label=label)
            b.connect("clicked", cb)
            bar.append(b)
            return b

        button("New", self._on_new)
        button("Open .fms", self._on_open_fms)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        button("▶ Play", self._on_play)
        button("❚❚ Pause", self._on_pause)
        button("Resume", self._on_resume)
        button("■ Stop", self._on_stop)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        button("+ Channel", self._on_add_channel)
        button("+ Pattern", self._on_add_pattern)

        bar.append(Gtk.Label(label="  BPM"))
        self.bpm_spin = Gtk.SpinButton.new_with_range(20, 400, 1)
        self.bpm_spin.set_value(self.song.bpm)
        self.bpm_spin.connect("value-changed", self._on_bpm)
        bar.append(self.bpm_spin)

        bar.append(Gtk.Label(label="  Pattern"))
        self.pattern_drop = Gtk.DropDown.new_from_strings(["Pattern 1"])
        self.pattern_drop.connect("notify::selected", self._on_pattern_changed)
        bar.append(self.pattern_drop)

        bar.append(Gtk.Label(label="  Instrument"))
        self.inst_drop = Gtk.DropDown.new_from_strings(gm.GM_NAMES)
        self.inst_drop.set_hexpand(True)
        self.inst_drop.connect("notify::selected", self._on_instrument_changed)
        bar.append(self.inst_drop)
        return bar

    # -- helpers -------------------------------------------------------------

    def _refresh_patterns(self):
        self._sync_guard = True
        names = [p.name for p in self.song.patterns]
        self.pattern_drop.set_model(Gtk.StringList.new(names or ["—"]))
        self.pattern_drop.set_selected(self.grid.pattern_index)
        self._sync_guard = False

    def _sync_instrument(self):
        """Reflect the channel under the cursor in the instrument dropdown."""
        if not self.song.channels:
            return
        col = min(self.grid.cursor_col, len(self.song.channels) - 1)
        self._sync_guard = True
        self.inst_drop.set_selected(self.song.channels[col].program)
        self._sync_guard = False

    def _update_status(self):
        sf = getattr(self.synth, "soundfont", None)
        audio = "fluidsynth" if self.synth.available else "SILENT (no fluidsynth/soundfont)"
        ch = self.song.channels[self.grid.cursor_col] if self.song.channels else None
        chname = ch.name if ch else "-"
        self.status.set_text(
            f"Oct {self.edit_octave}  |  Ch {self.grid.cursor_col + 1} ({chname})  |  "
            f"Row {self.grid.cursor_row:03d}  |  Audio: {audio}"
            + (f"  |  SF: {sf}" if sf else "")
        )

    def _advance_row(self):
        pat = self.grid.pattern
        if pat and self.grid.cursor_row < pat.rows - 1:
            self.grid.cursor_row += 1

    def _preview(self, midi):
        if self.seq.playing or not self.song.channels:
            return
        chan = self.song.channels[self.grid.cursor_col]
        self.synth.program_change(chan.midi_channel, chan.program)
        self.synth.note_on(chan.midi_channel, midi, 100)
        GLib.timeout_add(400, lambda: (self.synth.note_off(chan.midi_channel, midi), False)[1])

    # -- transport callbacks -------------------------------------------------

    def _on_play(self, *_):
        self.song.bpm = self.bpm_spin.get_value()
        self.seq.play(self.song, start_order=0, start_row=0)
        self._update_status()

    def _on_pause(self, *_):
        self.seq.pause()

    def _on_resume(self, *_):
        self.seq.resume()

    def _on_stop(self, *_):
        self.seq.stop()
        self.grid.playhead_row = -1
        self.grid.queue_draw()

    def _on_row_threadsafe(self, order_index, pattern_index, row):
        GLib.idle_add(self._on_row, order_index, pattern_index, row)

    def _on_row(self, order_index, pattern_index, row):
        self.grid.playhead_pattern = pattern_index
        self.grid.playhead_row = row
        self.grid.queue_draw()
        return False

    # -- edit callbacks ------------------------------------------------------

    def _on_new(self, *_):
        self.seq.stop()
        self.song = Song.new_default()
        self.edit_octave = 4
        self.grid.set_song(self.song)
        self.bpm_spin.set_value(self.song.bpm)
        self._refresh_patterns()
        self._sync_instrument()
        self._update_status()

    def _on_add_channel(self, *_):
        self.song.add_channel()
        self.grid.refresh()
        self._update_status()

    def _on_add_pattern(self, *_):
        idx = self.song.add_pattern()
        self.grid.pattern_index = idx
        self._refresh_patterns()
        self.grid.refresh()

    def _on_bpm(self, spin):
        self.song.bpm = spin.get_value()
        self._update_status()

    def _on_pattern_changed(self, drop, _param):
        if self._sync_guard:
            return
        self.grid.pattern_index = drop.get_selected()
        self.grid.cursor_row = 0
        self.grid.refresh()
        self._update_status()

    def _on_instrument_changed(self, drop, _param):
        if self._sync_guard or not self.song.channels:
            return
        col = min(self.grid.cursor_col, len(self.song.channels) - 1)
        prog = drop.get_selected()
        self.song.channels[col].program = prog
        self.synth.program_change(self.song.channels[col].midi_channel, prog)

    def _on_cell_clicked(self, col, row):
        self._sync_instrument()
        self._update_status()

    def _on_open_fms(self, *_):
        dialog = Gtk.FileChooserNative(
            title="Open FM-Song (.fms)", transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        flt = Gtk.FileFilter()
        flt.set_name("FM-Song files")
        flt.add_pattern("*.fms")
        flt.add_pattern("*.FMS")
        dialog.add_filter(flt)
        dialog.connect("response", self._on_open_fms_response)
        dialog.show()
        self._open_dialog = dialog          # keep a reference alive

    def _on_open_fms_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            gfile = dialog.get_file()
            if gfile:
                self._load_fms(gfile.get_path())
        dialog.destroy()
        self._open_dialog = None

    def _load_fms(self, path):
        try:
            song = fms.load_fms(path)
        except Exception as exc:                 # noqa: BLE001
            self.status.set_text(f"Failed to open {path}: {exc}")
            return
        self.seq.stop()
        self.song = song
        self.grid.set_song(song)
        self.bpm_spin.set_value(song.bpm)
        self._refresh_patterns()
        self._sync_instrument()
        self.status.set_text(
            f"Loaded {path}: {len(song.patterns)} pattern(s), "
            f"{len(song.channels)} channels, BPM {song.bpm:.0f}"
        )

    # -- keyboard ------------------------------------------------------------

    def _on_key(self, controller, keyval, keycode, state):
        name = Gdk.keyval_name(keyval) or ""
        pat = self.grid.pattern
        if not pat:
            return False
        col, row = self.grid.cursor_col, self.grid.cursor_row
        lower = name.lower()
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        # Ctrl + (Up/Down or +/-) : transpose the current cell by a semitone.
        if ctrl and name in ("Up", "Down", "plus", "minus",
                             "KP_Add", "KP_Subtract", "equal"):
            up = name in ("Up", "plus", "KP_Add", "equal")
            self._transpose_cell(+1 if up else -1)
            return True

        if name in ("Up", "Down", "Left", "Right"):
            if name == "Up":
                self.grid.cursor_row = max(0, row - 1)
            elif name == "Down":
                self.grid.cursor_row = min(pat.rows - 1, row + 1)
            elif name == "Left":
                self.grid.cursor_col = max(0, col - 1)
            else:
                self.grid.cursor_col = min(len(self.song.channels) - 1, col + 1)
            self._sync_octave_from_cell()
            self._sync_instrument()
            self.grid.queue_draw()
            self._update_status()
            return True

        if lower in NOTE_KEYS:
            midi = make_midi(NOTE_KEYS[lower], self.edit_octave)
            pat.data[col][row] = midi
            self._preview(midi)
            self._advance_row()
            self.grid.queue_draw()
            self._update_status()
            return True

        if name in ("plus", "KP_Add", "equal"):          # octave up (no Ctrl)
            self.edit_octave = min(8, self.edit_octave + 1)
            self._transpose_cell(+12, only_if_note=True)
            self._update_status()
            return True
        if name in ("minus", "KP_Subtract"):             # octave down (no Ctrl)
            self.edit_octave = max(0, self.edit_octave - 1)
            self._transpose_cell(-12, only_if_note=True)
            self._update_status()
            return True
        if name == "space":
            pat.data[col][row] = REST
            self._advance_row()
            self.grid.queue_draw()
            return True
        if name in ("Delete", "BackSpace"):
            pat.data[col][row] = None
            self.grid.queue_draw()
            return True
        return False

    def _transpose_cell(self, delta, only_if_note=False):
        pat = self.grid.pattern
        cell = pat.data[self.grid.cursor_col][self.grid.cursor_row]
        if isinstance(cell, int) and cell >= 0:
            pat.data[self.grid.cursor_col][self.grid.cursor_row] = max(0, min(127, cell + delta))
            self._preview(pat.data[self.grid.cursor_col][self.grid.cursor_row])
            self.grid.queue_draw()
        elif not only_if_note:
            pass

    def _sync_octave_from_cell(self):
        pat = self.grid.pattern
        cell = pat.data[self.grid.cursor_col][self.grid.cursor_row]
        if isinstance(cell, int) and cell >= 0:
            self.edit_octave = max(0, min(8, cell // 12 - 1))

    # -- shutdown ------------------------------------------------------------

    def _on_close(self, *_):
        self.seq.stop()
        self.synth.shutdown()
        return False


class FmTrackerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = FmTrackerWindow(self)
        win.present()


def main(argv=None):
    app = FmTrackerApp()
    return app.run(argv)
