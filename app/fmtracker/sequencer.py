"""Playback engine.

A background thread walks the order-list (pattern by pattern, row by row) at a
BPM-derived rate and drives the synth with note-on / note-off. The order-list
loops back to the start, matching the original FM-Song behaviour.

Timing uses a monotonic clock with drift correction; the thread never touches
GTK -- it reports the play position through ``on_row``, which the UI must
marshal onto the main loop (e.g. ``GLib.idle_add``).
"""

from __future__ import annotations

import threading
import time

from .model import REST, Song


class Sequencer:
    def __init__(self, synth):
        self.synth = synth
        self.song: Song | None = None
        self.on_row = None          # callback(order_index, pattern_index, row)
        self.loop = True
        self.playing = False
        self.paused = False

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._active: dict[int, int] = {}   # midi_channel -> currently sounding key

    # -- transport -----------------------------------------------------------

    def play(self, song: Song, start_order: int = 0, start_row: int = 0):
        self.stop()
        if not song.order or not song.patterns:
            return
        self.song = song
        self._stop.clear()
        self._pause.clear()
        self.playing = True
        self.paused = False
        self._apply_programs()
        self._thread = threading.Thread(
            target=self._run, args=(start_order, start_row), daemon=True
        )
        self._thread.start()

    def pause(self):
        if self.playing and not self.paused:
            self.paused = True
            self._pause.set()

    def resume(self):
        if self.playing and self.paused:
            self.paused = False
            self._pause.clear()

    def stop(self):
        self._stop.set()
        t = self._thread
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=1.0)
        self._thread = None
        self.playing = False
        self.paused = False
        self._all_off()

    # -- internals -----------------------------------------------------------

    def _apply_programs(self):
        for ch in self.song.channels:
            self.synth.program_change(ch.midi_channel, ch.program)

    def _all_off(self):
        for midi_ch, key in list(self._active.items()):
            self.synth.note_off(midi_ch, key)
        self._active.clear()
        self.synth.all_notes_off()

    def _run(self, start_order: int, start_row: int):
        song = self.song
        oi = max(0, min(start_order, len(song.order) - 1))
        row = start_row
        next_t = time.monotonic()

        while not self._stop.is_set():
            pidx = song.order[oi]
            pat = song.patterns[pidx]

            if row >= pat.rows:
                # advance to next order entry, looping back to the start.
                oi += 1
                row = 0
                if oi >= len(song.order):
                    if not self.loop:
                        break
                    oi = 0
                continue

            self._play_row(song, pat, row)
            if self.on_row:
                self.on_row(oi, pidx, row)

            next_t += song.row_seconds
            if not self._wait_until(next_t):
                break               # stopped
            if self._pause.is_set():
                self._handle_pause()
                next_t = time.monotonic()
            row += 1

        self._all_off()
        self.playing = False

    def _play_row(self, song, pat, row):
        for ch_index, chan in enumerate(song.channels):
            cell = pat.data[ch_index][row]
            if cell is None:
                continue                      # sustain / empty
            mc = chan.midi_channel
            prev = self._active.pop(mc, None)
            if prev is not None:
                self.synth.note_off(mc, prev)
            if cell == REST:
                continue                      # note-off only
            if not chan.mute:
                self.synth.note_on(mc, cell, 100)
                self._active[mc] = cell

    def _wait_until(self, target: float) -> bool:
        """Sleep until ``target`` (monotonic). Returns False if stopped."""
        while True:
            if self._stop.is_set():
                return False
            if self._pause.is_set():
                return True
            dt = target - time.monotonic()
            if dt <= 0:
                return True
            time.sleep(min(dt, 0.005))

    def _handle_pause(self):
        self._all_off()
        while self._pause.is_set() and not self._stop.is_set():
            time.sleep(0.01)
