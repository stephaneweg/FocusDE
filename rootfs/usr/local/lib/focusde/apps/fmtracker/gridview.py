"""The pattern grid widget (Cairo-drawn), with click-to-position support."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk        # noqa: E402

from .model import REST, midi_to_name   # noqa: E402

ROW_H = 20
COL_W = 78
HEAD_W = 52      # left gutter (row numbers)
HEAD_H = 26      # top header (channel names)

# Pastel palette (Focus DE look).
C_BG = (0.97, 0.96, 0.99)
C_HEADER = (0.90, 0.87, 0.95)
C_HEADER_SEL = (0.78, 0.69, 0.92)
C_GUTTER = (0.93, 0.91, 0.96)
C_GRID = (0.85, 0.82, 0.90)
C_CURSOR = (0.79, 0.71, 0.93)
C_PLAYHEAD = (1.00, 0.89, 0.70)
C_TEXT = (0.16, 0.14, 0.25)
C_TEXT_DIM = (0.60, 0.58, 0.66)
C_MUTE = (0.80, 0.45, 0.45)


class GridView(Gtk.DrawingArea):
    def __init__(self, on_cell_clicked=None):
        super().__init__()
        self.song = None
        self.pattern_index = 0
        self.cursor_row = 0
        self.cursor_col = 0
        self.playhead_row = -1
        self.playhead_pattern = -1
        self.on_cell_clicked = on_cell_clicked

        self.set_focusable(True)        # take keyboard focus (note entry lives here)
        self.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        self.add_controller(click)

    # -- state ---------------------------------------------------------------

    def set_song(self, song):
        self.song = song
        self.pattern_index = 0
        self.cursor_row = 0
        self.cursor_col = 0
        self._resize()
        self.queue_draw()

    @property
    def pattern(self):
        if not self.song or not self.song.patterns:
            return None
        self.pattern_index = max(0, min(self.pattern_index, len(self.song.patterns) - 1))
        return self.song.patterns[self.pattern_index]

    def _resize(self):
        pat = self.pattern
        if not pat:
            return
        self.set_content_width(HEAD_W + len(self.song.channels) * COL_W)
        self.set_content_height(HEAD_H + pat.rows * ROW_H)

    def refresh(self):
        self._resize()
        self.queue_draw()

    # -- input ---------------------------------------------------------------

    def _on_pressed(self, gesture, n_press, x, y):
        self.grab_focus()               # clicking the grid returns key focus to it
        pat = self.pattern
        if not pat:
            return
        if x < HEAD_W or y < HEAD_H:
            return
        col = int((x - HEAD_W) // COL_W)
        row = int((y - HEAD_H) // ROW_H)
        if 0 <= col < len(self.song.channels) and 0 <= row < pat.rows:
            self.cursor_col = col
            self.cursor_row = row
            self.queue_draw()
            if self.on_cell_clicked:
                self.on_cell_clicked(col, row)

    # -- drawing -------------------------------------------------------------

    def _draw(self, area, cr, width, height):
        cr.set_source_rgb(*C_BG)
        cr.paint()
        pat = self.pattern
        if not pat:
            return
        song = self.song
        n_ch = len(song.channels)
        cr.select_font_face("monospace")
        cr.set_font_size(13)

        on_this_pattern = self.playhead_pattern == self.pattern_index

        # playhead row band
        if on_this_pattern and 0 <= self.playhead_row < pat.rows:
            y = HEAD_H + self.playhead_row * ROW_H
            cr.set_source_rgb(*C_PLAYHEAD)
            cr.rectangle(0, y, width, ROW_H)
            cr.fill()

        # cursor cell
        cx = HEAD_W + self.cursor_col * COL_W
        cy = HEAD_H + self.cursor_row * ROW_H
        cr.set_source_rgb(*C_CURSOR)
        cr.rectangle(cx, cy, COL_W, ROW_H)
        cr.fill()

        # gutter + rows
        for row in range(pat.rows):
            y = HEAD_H + row * ROW_H
            cr.set_source_rgb(*C_GUTTER)
            cr.rectangle(0, y, HEAD_W, ROW_H)
            cr.fill()
            cr.set_source_rgb(*(C_TEXT if row % 4 == 0 else C_TEXT_DIM))
            cr.move_to(8, y + 14)
            cr.show_text(f"{row:03d}")

            for col in range(n_ch):
                cell = pat.data[col][row]
                x = HEAD_W + col * COL_W
                if cell is None:
                    cr.set_source_rgb(*C_TEXT_DIM)
                    text = "···"
                elif cell == REST:
                    cr.set_source_rgb(*C_TEXT_DIM)
                    text = "==="
                else:
                    cr.set_source_rgb(*C_TEXT)
                    text = midi_to_name(cell)
                cr.move_to(x + 10, y + 14)
                cr.show_text(text)

        # grid lines
        cr.set_source_rgb(*C_GRID)
        cr.set_line_width(1)
        for col in range(n_ch + 1):
            x = HEAD_W + col * COL_W
            cr.move_to(x, 0)
            cr.line_to(x, HEAD_H + pat.rows * ROW_H)
        cr.move_to(HEAD_W, 0)
        cr.line_to(HEAD_W, HEAD_H + pat.rows * ROW_H)
        cr.stroke()

        # header (channel names) on top, drawn last so it stays visible
        cr.set_source_rgb(*C_HEADER)
        cr.rectangle(0, 0, width, HEAD_H)
        cr.fill()
        for col in range(n_ch):
            x = HEAD_W + col * COL_W
            chan = song.channels[col]
            if col == self.cursor_col:
                cr.set_source_rgb(*C_HEADER_SEL)
                cr.rectangle(x, 0, COL_W, HEAD_H)
                cr.fill()
            cr.set_source_rgb(*(C_MUTE if chan.mute else C_TEXT))
            cr.move_to(x + 6, 17)
            name = chan.name if len(chan.name) <= 9 else chan.name[:9]
            cr.show_text(("M " if chan.mute else "") + name)
