"""GTK4 application: window, toolbar, keyboard/mouse wiring."""

from __future__ import annotations

import json
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import GLib, Gdk, Gtk      # noqa: E402

from . import export, fms, gm                  # noqa: E402
from .gridview import GridView, ROW_H, HEAD_H   # noqa: E402
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
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_vexpand(True)
        self.scroller.set_hexpand(True)
        self.scroller.set_child(self.grid)
        root.append(self.scroller)

        self.status = Gtk.Label(xalign=0)
        self.status.set_margin_start(8)
        self.status.set_margin_top(2)
        self.status.set_margin_bottom(4)
        root.append(self.status)

        # Keys go to the grid, so toolbar buttons never steal Space/Enter; the
        # grid grabs focus when shown and on click.
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.grid.add_controller(keys)
        self.grid.connect("map", lambda *_: self.grid.grab_focus())

        self.connect("close-request", self._on_close)
        self._refresh_patterns()
        self._sync_instrument()
        self._update_status()

    # -- UI construction -----------------------------------------------------

    def _build_toolbar(self):
        # FlowBox so the controls wrap onto several rows on a narrow screen.
        bar = Gtk.FlowBox()
        bar.set_selection_mode(Gtk.SelectionMode.NONE)
        bar.set_max_children_per_line(30)
        bar.set_min_children_per_line(1)
        bar.set_column_spacing(6)
        bar.set_row_spacing(4)
        bar.set_homogeneous(False)
        for m in ("start", "end", "top", "bottom"):
            getattr(bar, f"set_margin_{m}")(6)

        def button(label, cb):
            b = Gtk.Button(label=label)
            b.set_focusable(False)          # never steal Space/Enter from the grid
            b.connect("clicked", cb)
            return b

        def group(*widgets):
            g = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            for w in widgets:
                g.append(w)
            bar.insert(g, -1)

        group(button("New", self._on_new), button("Open", self._on_open_project),
              button("Save", self._on_save_project),
              button("Import .fms", self._on_open_fms), self._export_button())
        group(button("▶ Play", self._on_play), button("❚❚ Pause", self._on_pause),
              button("Resume", self._on_resume), button("■ Stop", self._on_stop))
        group(button("+ Channel", self._on_add_channel),
              button("+ Pattern", self._on_add_pattern))

        self.bpm_spin = Gtk.SpinButton.new_with_range(20, 400, 1)
        self.bpm_spin.set_value(self.song.bpm)
        self.bpm_spin.connect("value-changed", self._on_bpm)
        group(Gtk.Label(label="BPM"), self.bpm_spin)

        self.pattern_drop = Gtk.DropDown.new_from_strings(["Pattern 1"])
        self.pattern_drop.connect("notify::selected", self._on_pattern_changed)
        group(Gtk.Label(label="Pattern"), self.pattern_drop)

        self.inst_drop = Gtk.DropDown.new_from_strings(gm.GM_NAMES)
        self.inst_drop.connect("notify::selected", self._on_instrument_changed)
        group(Gtk.Label(label="Instrument"), self.inst_drop)
        return bar

    def _export_button(self):
        btn = Gtk.MenuButton(label="Export ▾")
        btn.set_focusable(False)
        pop = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for m in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{m}")(6)
        for label, fmt, ext in (("MIDI (.mid)", "midi", "mid"),
                                ("WAV (.wav)", "wav", "wav"),
                                ("MP3 (.mp3)", "mp3", "mp3"),
                                ("MuseScore (.mscx)", "musescore", "mscx")):
            b = Gtk.Button(label=label)
            b.connect("clicked", self._on_export, fmt, ext, pop)
            box.append(b)
        pop.set_child(box)
        btn.set_popover(pop)
        return btn

    def _on_export(self, _b, fmt, ext, pop):
        pop.popdown()
        name = (self.song.title or "song").strip() or "song"
        dlg = Gtk.FileChooserNative(title="Export %s" % fmt.upper(),
                                    transient_for=self, action=Gtk.FileChooserAction.SAVE)
        dlg.set_current_name("%s.%s" % (name, ext))
        dlg.connect("response", self._on_export_response, fmt)
        dlg.show()
        self._export_dialog = dlg

    def _on_export_response(self, dlg, response, fmt):
        if response == Gtk.ResponseType.ACCEPT:
            gf = dlg.get_file()
            if gf:
                self.status.set_text("Exporting %s…" % fmt.upper())
                threading.Thread(target=self._do_export, args=(gf.get_path(), fmt),
                                 daemon=True).start()
        dlg.destroy()
        self._export_dialog = None

    def _do_export(self, path, fmt):
        try:
            out = export.export(self.song, path, fmt)
            GLib.idle_add(self.status.set_text, "Exported: " + out)
        except Exception as exc:                 # noqa: BLE001
            GLib.idle_add(self.status.set_text, "Export failed (%s): %s" % (fmt, exc))

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

    def _ensure_row_visible(self, row):
        adj = self.scroller.get_vadjustment()
        if adj is None:
            return
        page = adj.get_page_size()
        if page <= 0:
            return
        y = HEAD_H + row * ROW_H
        top = adj.get_value()
        if y < top:
            adj.set_value(max(0, y))
        elif y + ROW_H > top + page:
            adj.set_value(min(adj.get_upper() - page, y + ROW_H - page))

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
        # follow the song across patterns, and keep the playhead in view
        if pattern_index != self.grid.pattern_index:
            self.grid.pattern_index = pattern_index
            self._refresh_patterns()
            self.grid.refresh()
        self.grid.playhead_pattern = pattern_index
        self.grid.playhead_row = row
        self._ensure_row_visible(row)
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
        self._ensure_row_visible(row)
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

    # -- native project save / open (lossless, .fmtrk JSON) ------------------

    def _on_save_project(self, *_):
        name = (self.song.title or "song").strip() or "song"
        dlg = Gtk.FileChooserNative(title="Save project", transient_for=self,
                                    action=Gtk.FileChooserAction.SAVE)
        dlg.set_current_name(name + ".fmtrk")
        dlg.connect("response", self._on_save_response)
        dlg.show()
        self._save_dialog = dlg

    def _on_save_response(self, dlg, response):
        if response == Gtk.ResponseType.ACCEPT:
            gf = dlg.get_file()
            if gf:
                try:
                    with open(gf.get_path(), "w", encoding="utf-8") as f:
                        json.dump(self.song.to_dict(), f, ensure_ascii=False, indent=1)
                    self.status.set_text("Saved: " + gf.get_path())
                except Exception as exc:                 # noqa: BLE001
                    self.status.set_text("Save failed: %s" % exc)
        dlg.destroy()
        self._save_dialog = None

    def _on_open_project(self, *_):
        dlg = Gtk.FileChooserNative(title="Open project (.fmtrk)", transient_for=self,
                                    action=Gtk.FileChooserAction.OPEN)
        flt = Gtk.FileFilter()
        flt.set_name("FM-Tracker project")
        flt.add_pattern("*.fmtrk")
        dlg.add_filter(flt)
        dlg.connect("response", self._on_open_project_response)
        dlg.show()
        self._open_proj_dialog = dlg

    def _on_open_project_response(self, dlg, response):
        if response == Gtk.ResponseType.ACCEPT:
            gf = dlg.get_file()
            if gf:
                try:
                    with open(gf.get_path(), encoding="utf-8") as f:
                        song = Song.from_dict(json.load(f))
                    self.seq.stop()
                    self.song = song
                    self.grid.set_song(song)
                    self.bpm_spin.set_value(song.bpm)
                    self._refresh_patterns()
                    self._sync_instrument()
                    self.status.set_text("Opened: " + gf.get_path())
                except Exception as exc:                 # noqa: BLE001
                    self.status.set_text("Open failed: %s" % exc)
        dlg.destroy()
        self._open_proj_dialog = None

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
            self._ensure_row_visible(self.grid.cursor_row)
            self.grid.queue_draw()
            self._update_status()
            return True

        if lower in NOTE_KEYS:
            midi = make_midi(NOTE_KEYS[lower], self.edit_octave)
            pat.data[col][row] = midi
            self._preview(midi)
            self._advance_row()
            self._ensure_row_visible(self.grid.cursor_row)
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
            self._ensure_row_visible(self.grid.cursor_row)
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
    def __init__(self, open_file=None):
        super().__init__(application_id=APP_ID)
        self.open_file = open_file

    def do_activate(self):
        win = FmTrackerWindow(self)
        if self.open_file:
            win._load_fms(self.open_file)
        win.present()


def main(argv=None):
    import os
    import sys
    argv = argv if argv is not None else sys.argv
    open_file = next((a for a in argv[1:]
                      if a.lower().endswith(".fms") and os.path.exists(a)), None)
    app = FmTrackerApp(open_file=open_file)
    return app.run([argv[0]])     # don't let GTK parse the .fms path
