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


def midi_to_musescore(midi_path: str, out_path: str) -> str:
    for exe in ("mscore", "musescore", "musescore4", "musescore3", "mscore4", "mscore3"):
        p = shutil.which(exe)
        if p:
            subprocess.run([p, "-o", out_path, midi_path],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return out_path
    raise RuntimeError("MuseScore (mscore) is not installed — the .mid opens in MuseScore directly")


def export(song: Song, path: str, fmt: str) -> str:
    """fmt in {'midi','wav','mp3','musescore'}. Returns the written path."""
    if fmt == "midi":
        return write_midi(song, path)
    with tempfile.TemporaryDirectory() as tmp:
        mid = os.path.join(tmp, "song.mid")
        write_midi(song, mid)
        if fmt == "wav":
            return render_wav(mid, path)
        if fmt == "mp3":
            wav = os.path.join(tmp, "song.wav")
            render_wav(mid, wav)
            return wav_to_mp3(wav, path)
        if fmt == "musescore":
            return midi_to_musescore(mid, path)
    raise ValueError("unknown format: %s" % fmt)
