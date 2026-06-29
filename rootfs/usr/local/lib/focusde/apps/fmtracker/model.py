"""Song data model.

A song is a list of *channels* (the instruments, song-global), a list of
*patterns* (grids of notes), and an *order list* of pattern indices that is
played in sequence and loops back to the start -- the original FM-Song model.

Cell values:
    None        -> empty / sustain (display "----")
    REST (-1)   -> note-off (display "===")
    >= 0        -> MIDI note number
"""

from __future__ import annotations

REST = -1

#: MIDI note number of the lowest note an .fms "octave 0, C" maps to (C1).
FMS_BASE_MIDI = 24

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_name(midi: int) -> str:
    """Return e.g. "C-4" / "F#5" for a MIDI note number."""
    octave = midi // 12 - 1          # MIDI 60 = C4
    name = NOTE_NAMES[midi % 12]
    if len(name) == 1:
        return f"{name}-{octave}"
    return f"{name}{octave}"


def make_midi(semitone: int, octave: int) -> int:
    """semitone 0..11, octave in MIDI sense (C4 == 60). Clamped to 0..127."""
    return max(0, min(127, (octave + 1) * 12 + semitone))


class Channel:
    """A song-global instrument / track."""

    def __init__(self, name: str, midi_channel: int, program: int = 0):
        self.name = name
        self.midi_channel = midi_channel   # 0..15
        self.program = program             # GM program 0..127
        self.mute = False

    def to_dict(self):
        return {
            "name": self.name,
            "midi_channel": self.midi_channel,
            "program": self.program,
            "mute": self.mute,
        }

    @classmethod
    def from_dict(cls, d):
        c = cls(d["name"], d["midi_channel"], d.get("program", 0))
        c.mute = d.get("mute", False)
        return c


class Pattern:
    """A grid: ``data[channel_index][row]`` -> None | REST | midi."""

    def __init__(self, name: str, rows: int, n_channels: int):
        self.name = name
        self.rows = rows
        self.data = [[None] * rows for _ in range(n_channels)]

    def add_channel_column(self):
        self.data.append([None] * self.rows)

    def remove_channel_column(self, index: int):
        if 0 <= index < len(self.data):
            del self.data[index]

    def get(self, ch: int, row: int):
        return self.data[ch][row]

    def set(self, ch: int, row: int, value):
        self.data[ch][row] = value

    def to_dict(self):
        return {"name": self.name, "rows": self.rows, "data": self.data}

    @classmethod
    def from_dict(cls, d):
        p = cls.__new__(cls)
        p.name = d["name"]
        p.rows = d["rows"]
        p.data = d["data"]
        return p


class Song:
    def __init__(self):
        self.title: str = ""
        self.author: str = ""
        self.comment: str = ""
        self.channels: list[Channel] = []
        self.patterns: list[Pattern] = []
        self.order: list[int] = []
        self.bpm: float = 120.0
        self.rows_per_beat: int = 4          # 16th-note rows

    # -- construction helpers ------------------------------------------------

    @classmethod
    def new_default(cls, n_channels: int = 4, rows: int = 64):
        song = cls()
        for i in range(n_channels):
            song.channels.append(Channel(f"Ch {i + 1}", midi_channel=i, program=0))
        song.patterns.append(Pattern("Pattern 1", rows, n_channels))
        song.order = [0]
        return song

    def add_channel(self, name: str | None = None, program: int = 0):
        idx = len(self.channels)
        midi_channel = idx % 16
        self.channels.append(Channel(name or f"Ch {idx + 1}", midi_channel, program))
        for p in self.patterns:
            p.add_channel_column()
        return idx

    def add_pattern(self, rows: int | None = None):
        rows = rows or (self.patterns[0].rows if self.patterns else 64)
        p = Pattern(f"Pattern {len(self.patterns) + 1}", rows, len(self.channels))
        self.patterns.append(p)
        self.order.append(len(self.patterns) - 1)
        return len(self.patterns) - 1

    @property
    def row_seconds(self) -> float:
        return 60.0 / self.bpm / self.rows_per_beat

    # -- persistence (native project JSON) -----------------------------------

    def to_dict(self):
        return {
            "version": 1,
            "bpm": self.bpm,
            "rows_per_beat": self.rows_per_beat,
            "channels": [c.to_dict() for c in self.channels],
            "patterns": [p.to_dict() for p in self.patterns],
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, d):
        song = cls()
        song.bpm = d.get("bpm", 120.0)
        song.rows_per_beat = d.get("rows_per_beat", 4)
        song.channels = [Channel.from_dict(c) for c in d["channels"]]
        song.patterns = [Pattern.from_dict(p) for p in d["patterns"]]
        song.order = d.get("order", list(range(len(song.patterns))))
        return song
