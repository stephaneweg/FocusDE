"""Importer for legacy FM-Song ``.fms`` files.

Format (authoritative: the original ``OpenFMS`` reader (FM-Song) + QBasic ``FMLIB.BAS``):

    char[15]  signature  "fm-song-project"
    char[20]  name
    char[20]  author
    char[50]  comment
    int16     maxtrack
    instrument[8]:
        char[8] name
        uint8   x26   (OPL2 operator params: attack1/2, decay1/2, sustain1/2,
                       release1/2, output1/2, scaling1/2, amp-vibrato1/2,
                       pitch-vibrato1/2, freq-mult1/2, env-scaling1/2,
                       waveselect1/2, feedback, connection, sustain-level1/2)
    track[maxtrack]:
        int16   notes-per-channel (mNotes)
        int16   trackdelay
        uint8   channel-enabled x8
        uint8   note  x (8 * mNotes)        channel-major

Note byte: bit7 rest, bit6 sharp, bits5-3 octave, bits2-0 diatonic (1=C..7=B).

Instruments hold OPL register data, not a GM program; we default to piano and
use a name-based heuristic (see :mod:`.gm`) to guess a closer preset.
"""

from __future__ import annotations

import struct

from . import gm
from .model import FMS_BASE_MIDI, REST, Channel, Pattern, Song

SIGNATURE = b"fm-song-project"

# anote (1..7) -> 1-based semitone within the octave. Sharp applies to all but "mi".
_ANOTE_BASE = {1: 1, 2: 3, 3: 5, 4: 6, 5: 8, 6: 10, 7: 12}


class FmsError(Exception):
    pass


class _Reader:
    def __init__(self, data: bytes):
        self.d = data
        self.p = 0

    def take(self, n: int) -> bytes:
        if self.p + n > len(self.d):
            raise FmsError("unexpected end of file")
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def cstr(self, n: int) -> str:
        raw = self.take(n)
        return raw.split(b"\x00", 1)[0].decode("latin-1", "replace").strip()

    def u8(self) -> int:
        return self.take(1)[0]

    def i16(self) -> int:
        return struct.unpack("<h", self.take(2))[0]


def _decode_note(v: int):
    """Return None (empty), REST, or a MIDI note number."""
    if (v >> 7) & 1:
        return REST
    anote = v & 7
    if anote == 0:
        return None
    octave = (v >> 3) & 7
    sharp = (v >> 6) & 1
    base1 = _ANOTE_BASE[anote]
    if anote != 3:          # "mi" (E) carries no sharp in the original
        base1 += sharp
    note_value = base1 + 12 * octave          # 1-based semitone incl. octave
    return max(0, min(127, (note_value - 1) + FMS_BASE_MIDI))


def load_fms(path: str) -> Song:
    with open(path, "rb") as f:
        data = f.read()
    return parse_fms(data)


def parse_fms(data: bytes) -> Song:
    r = _Reader(data)

    sig = r.take(15)
    if sig != SIGNATURE:
        raise FmsError(f"not an FM-Song file (bad signature {sig!r})")

    name = r.cstr(20)
    author = r.cstr(20)
    comment = r.cstr(50)
    maxtrack = r.i16()
    if maxtrack <= 0 or maxtrack > 1024:
        raise FmsError(f"implausible track count: {maxtrack}")

    song = Song()
    song.title = name
    song.author = author
    song.comment = comment
    song.rows_per_beat = 4

    # 8 instruments -> 8 channels.
    for i in range(8):
        iname = r.cstr(8)
        r.take(26)                                  # OPL operator params (unused)
        program = gm.guess_program(iname)
        song.channels.append(
            Channel(iname or f"Inst {i + 1}", midi_channel=i % 16, program=program)
        )

    first_delay = None
    try:
        for _t in range(maxtrack):
            mnotes = r.i16()
            delay = r.i16()
            if first_delay is None and delay > 0:
                first_delay = delay
            r.take(8)                               # channel-enabled flags (unused)
            if mnotes < 0 or mnotes > 100000:
                raise FmsError(f"implausible note count: {mnotes}")

            pat = Pattern(f"Pattern {_t + 1}", mnotes, len(song.channels))
            truncated = False
            for ch in range(8):
                for row in range(mnotes):
                    try:
                        pat.data[ch][row] = _decode_note(r.u8())
                    except FmsError:
                        truncated = True       # leave the rest empty (None)
                        break
                if truncated:
                    break
            song.patterns.append(pat)
            if truncated:
                break
    except FmsError:
        # Truncated file: keep the complete tracks parsed so far.
        if not song.patterns:
            raise

    song.order = list(range(len(song.patterns)))

    # Per-track tempo isn't modelled yet; derive a global BPM from the first track.
    # trackdelay/20 == seconds per row  ->  bpm = 60 / (rowsec * rows_per_beat).
    if first_delay:
        rowsec = first_delay / 20.0
        song.bpm = max(20.0, min(400.0, 60.0 / (rowsec * song.rows_per_beat)))

    if not song.patterns:
        raise FmsError("file contains no tracks")
    return song
