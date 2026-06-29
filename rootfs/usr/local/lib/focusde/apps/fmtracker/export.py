"""Export a Song to MIDI / WAV / MP3 / MuseScore.

- **MIDI** is written natively (a Standard MIDI File, format 1) from the song model.
- **WAV** renders that MIDI through fluidsynth + the General-MIDI SoundFont.
- **MP3** re-encodes the WAV with ffmpeg (or lame).
- **MuseScore** converts the MIDI with the MuseScore CLI (mscore) — MuseScore also
  opens the plain `.mid` directly.

Everything but MIDI shells out to external tools; each raises a clear error if the
tool (or a SoundFont) is missing, so the caller can report it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from . import synth as synthmod
from .model import REST, Song

PPQ = 480     # MIDI ticks per quarter note


def _vlq(n: int) -> bytes:
    """MIDI variable-length quantity."""
    out = bytearray([n & 0x7F])
    n >>= 7
    while n > 0:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def write_midi(song: Song, path: str) -> str:
    """Render the whole song (following the order-list) to a Standard MIDI File."""
    tpr = max(1, PPQ // max(1, song.rows_per_beat))     # ticks per row
    n_ch = len(song.channels)
    events = [[] for _ in range(n_ch)]                  # per channel: (tick, status, d1, d2)
    active = [None] * n_ch
    grow = 0
    order = song.order or list(range(len(song.patterns)))
    for pidx in order:
        if not (0 <= pidx < len(song.patterns)):
            continue
        pat = song.patterns[pidx]
        for row in range(pat.rows):
            tick = grow * tpr
            for ch in range(n_ch):
                cell = pat.data[ch][row] if ch < len(pat.data) else None
                if cell is None:
                    continue
                mc = song.channels[ch].midi_channel
                if active[ch] is not None:
                    events[ch].append((tick, 0x80 | mc, active[ch], 0))
                    active[ch] = None
                if cell == REST:
                    continue
                if 0 <= cell <= 127:
                    events[ch].append((tick, 0x90 | mc, cell, 100))
                    active[ch] = cell
            grow += 1
    end_tick = grow * tpr
    for ch in range(n_ch):
        if active[ch] is not None:
            events[ch].append((end_tick, 0x80 | song.channels[ch].midi_channel, active[ch], 0))

    tracks = []
    tempo = int(60_000_000 / max(1.0, song.bpm))        # microseconds per quarter
    meta = _vlq(0) + b"\xFF\x51\x03" + tempo.to_bytes(3, "big")
    meta += _vlq(0) + b"\xFF\x2F\x00"
    tracks.append(meta)
    for ch in range(n_ch):
        mc = song.channels[ch].midi_channel
        data = _vlq(0) + bytes([0xC0 | mc, song.channels[ch].program & 0x7F])
        last = 0
        for tick, status, d1, d2 in sorted(events[ch], key=lambda e: e[0]):
            data += _vlq(tick - last) + bytes([status, d1, d2])
            last = tick
        data += _vlq(0) + b"\xFF\x2F\x00"
        tracks.append(data)

    with open(path, "wb") as f:
        f.write(b"MThd" + (6).to_bytes(4, "big") + (1).to_bytes(2, "big")
                + len(tracks).to_bytes(2, "big") + PPQ.to_bytes(2, "big"))
        for t in tracks:
            f.write(b"MTrk" + len(t).to_bytes(4, "big") + t)
    return path


def render_wav(midi_path: str, wav_path: str, soundfont: str | None = None, rate: int = 44100) -> str:
    sf = soundfont or synthmod.find_default_soundfont()
    if not sf:
        raise RuntimeError("no SoundFont found (install fluid-soundfont-gm)")
    fs = shutil.which("fluidsynth")
    if not fs:
        raise RuntimeError("fluidsynth is not installed")
    subprocess.run([fs, "-ni", "-g", "0.8", "-r", str(rate), "-F", wav_path, sf, midi_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def wav_to_mp3(wav_path: str, mp3_path: str) -> str:
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif shutil.which("lame"):
        subprocess.run(["lame", "-b", "192", wav_path, mp3_path],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        raise RuntimeError("need ffmpeg or lame to make MP3")
    return mp3_path


# ----- native MuseScore .mscx (ported from the author's C# MuseScoreExporter) --------
#
# Writes an uncompressed MuseScore-3 XML score (opens in MuseScore 3/4) — no mscore CLI.
# One channel = one staff, with a clef picked from the track's range. Durations snap to
# the 1/32 grid (triplets approximated, notes re-articulated across bar lines, no ties).

_U = 24     # integer units per quarter (1/32 == 3 units)
_VALS = [(96, "whole", 0), (72, "half", 1), (48, "half", 0), (36, "quarter", 1),
         (24, "quarter", 0), (18, "eighth", 1), (12, "eighth", 0), (9, "16th", 1),
         (6, "16th", 0), (3, "32nd", 0)]
_SHARP = [14, 21, 16, 23, 18, 13, 20, 15, 22, 17, 24, 19]
_FLAT = [14, 9, 16, 11, 18, 13, 8, 15, 10, 17, 12, 19]


def _r3(beats: float) -> int:
    u = round(beats * _U)
    return max(0, round(u / 3.0) * 3)


def _decompose(length: int):
    out = []
    r = max(0, (length // 3) * 3)
    guard = 0
    while r >= 3 and guard < 64:
        guard += 1
        for u, name, dots in _VALS:
            if u <= r:
                out.append((name, dots)); r -= u; break
    return out or [("32nd", 0)]


def _tpc(midi: int, center_fifths: int = 0) -> int:
    pc = midi % 12
    s, f = _SHARP[pc], _FLAT[pc]
    if s == f:
        return s
    center = 14 + center_fifths
    ds, df = abs(s - center), abs(f - center)
    if ds != df:
        return s if ds < df else f
    return f if center_fifths < 0 else s


def _clef_for(pitches) -> str:
    if not pitches:
        return "G"
    c = sum(pitches) / len(pitches)
    return "F" if c < 59 else "G"     # below ~B3 -> bass clef, else treble


def _xesc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _song_tracks(song: Song):
    """Per channel: a list of (start_u, len_u, midi), monophonic, over the whole song."""
    rpb = max(1, song.rows_per_beat)
    n_ch = len(song.channels)
    tracks = [[] for _ in range(n_ch)]
    active = [None] * n_ch
    grow = 0
    order = song.order or list(range(len(song.patterns)))
    for pidx in order:
        if not (0 <= pidx < len(song.patterns)):
            continue
        pat = song.patterns[pidx]
        for _row in range(pat.rows):
            for ch in range(n_ch):
                cell = pat.data[ch][_row] if ch < len(pat.data) else None
                if cell is None:
                    continue
                if active[ch] is not None:
                    s, m = active[ch]
                    tracks[ch].append((_r3(s / rpb), max(3, _r3((grow - s) / rpb)), m))
                    active[ch] = None
                if cell == REST:
                    continue
                if 0 <= cell <= 127:
                    active[ch] = (grow, cell)
            grow += 1
    for ch in range(n_ch):
        if active[ch] is not None:
            s, m = active[ch]
            tracks[ch].append((_r3(s / rpb), max(3, _r3((grow - s) / rpb)), m))
    return tracks, grow, rpb


def _emit_chord(out, pitches, length):
    for name, dots in _decompose(length):
        out.append("          <Chord>")
        if dots > 0:
            out.append("            <dots>%d</dots>" % dots)
        out.append("            <durationType>%s</durationType>" % name)
        for p in pitches:
            out.append("            <Note><pitch>%d</pitch><tpc>%d</tpc></Note>" % (p, _tpc(p)))
        out.append("          </Chord>")


def _emit_rest(out, length):
    for name, dots in _decompose(length):
        out.append("          <Rest>")
        if dots > 0:
            out.append("            <dots>%d</dots>" % dots)
        out.append("            <durationType>%s</durationType>" % name)
        out.append("          </Rest>")


def _write_staff(out, notes, measures, bar_units, sigN, sigD, clef):
    chords = [(s, l, [m]) for (s, l, m) in notes]      # monophonic -> one pitch per chord
    ci = 0
    for mi in range(measures):
        ms, me = mi * bar_units, mi * bar_units + bar_units
        out.append("      <Measure>")
        out.append("        <voice>")
        if mi == 0:
            out.append('          <Clef><concertClefType>%s</concertClefType>'
                       '<transposingClefType>%s</transposingClefType></Clef>' % (clef, clef))
            out.append("          <KeySig><accidental>0</accidental></KeySig>")
            out.append("          <TimeSig><sigN>%d</sigN><sigD>%d</sigD></TimeSig>" % (sigN, sigD))
        pos = ms
        while ci < len(chords) and chords[ci][0] < me:
            cstart, clen, pitches = chords[ci]
            cs = max(cstart, pos)
            nxt = chords[ci + 1][0] if ci + 1 < len(chords) else me
            if cs > pos:
                _emit_rest(out, cs - pos)
            cend = min(min(cstart + clen, me), max(nxt, cs + 3))
            if cend > cs:
                _emit_chord(out, pitches, cend - cs); pos = cend
            if cstart + clen > me:
                break
            ci += 1
        if pos < me:
            _emit_rest(out, me - pos)
        out.append("        </voice>")
        out.append("      </Measure>")


def write_mscx(song: Song, path: str, num: int = 4, den: int = 4) -> str:
    """Write a native MuseScore-3 .mscx: one staff per channel, clef from each range."""
    sigN, sigD = max(1, num), (8 if den == 8 else 4)
    bar_units = sigN * 96 // sigD
    tracks, _grow, _rpb = _song_tracks(song)
    n_ch = len(song.channels)

    measures = 1
    for t in tracks:
        if t:
            measures = max(measures, (t[-1][0] + t[-1][1] + bar_units - 1) // bar_units)

    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<museScore version="3.02">',
           "  <Score>", "    <Division>480</Division>"]
    for i in range(n_ch):
        nm = _xesc(song.channels[i].name or ("Voix %d" % (i + 1)))
        prog = max(0, min(127, song.channels[i].program))
        out += ["    <Part>", '      <Staff id="%d">' % (i + 1),
                '        <StaffType group="pitched"><name>stdNormal</name></StaffType>',
                "      </Staff>", "      <trackName>%s</trackName>" % nm,
                "      <Instrument>", "        <longName>%s</longName>" % nm,
                "        <Channel>", '          <program value="%d"/>' % prog,
                "        </Channel>", "      </Instrument>", "    </Part>"]
    for i in range(n_ch):
        clef = _clef_for([m for _, _, m in tracks[i]])
        out.append('    <Staff id="%d">' % (i + 1))
        if i == 0 and (song.title or "").strip():
            out += ["      <VBox>", "        <height>10</height>",
                    "        <Text><style>Title</style><text>%s</text></Text>" % _xesc(song.title.strip()),
                    "      </VBox>"]
        _write_staff(out, tracks[i], measures, bar_units, sigN, sigD, clef)
        out.append("    </Staff>")
    out += ["  </Score>", "</museScore>"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return path


def export(song: Song, path: str, fmt: str) -> str:
    """fmt in {'midi','wav','mp3','musescore'}. Returns the written path."""
    if fmt == "midi":
        return write_midi(song, path)
    if fmt == "musescore":
        return write_mscx(song, path)
    with tempfile.TemporaryDirectory() as tmp:
        mid = write_midi(song, os.path.join(tmp, "song.mid"))
        if fmt == "wav":
            return render_wav(mid, path)
        if fmt == "mp3":
            return wav_to_mp3(render_wav(mid, os.path.join(tmp, "song.wav")), path)
    raise ValueError("unknown format: %s" % fmt)
