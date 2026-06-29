"""Thin ctypes wrapper around libfluidsynth.

We bind only what a tracker needs: load a SoundFont, select GM programs, and
fire note-on / note-off. fluidsynth renders audio itself through its built-in
driver (PipeWire / PulseAudio / ALSA / JACK) -- no external synth process.

If libfluidsynth or a SoundFont is missing, the Synth degrades to a silent
no-op so the rest of the app still runs.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os

_LIB_CANDIDATES = [
    "libfluidsynth.so.3", "libfluidsynth.so.2", "libfluidsynth.so",
    "libfluidsynth-3.dll", "libfluidsynth.dll", "libfluidsynth.3.dylib",
]

# Common locations for a General-MIDI SoundFont on Debian/Ubuntu/Arch/Fedora.
_SF2_CANDIDATES = [
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/sounds/sf2/default-GM.sf2",
    "/usr/share/soundfonts/FluidR3_GM.sf2",
    "/usr/share/soundfonts/default.sf2",
    "/usr/share/sounds/sf2/TimGM6mb.sf2",
]


def _load_library():
    for name in _LIB_CANDIDATES:
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    found = ctypes.util.find_library("fluidsynth")
    if found:
        try:
            return ctypes.CDLL(found)
        except OSError:
            pass
    return None


def find_default_soundfont() -> str | None:
    env = os.environ.get("FMTRACKER_SOUNDFONT")
    if env and os.path.exists(env):
        return env
    for p in _SF2_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


class Synth:
    def __init__(self, soundfont: str | None = None, audio_driver: str | None = None):
        self.available = False
        self._lib = _load_library()
        self._settings = None
        self._synth = None
        self._driver = None
        self._sfont_id = -1
        if self._lib is None:
            print("[synth] libfluidsynth not found -> running silent")
            return
        self._bind()
        try:
            self._start(soundfont, audio_driver)
            self.available = True
        except Exception as exc:                    # noqa: BLE001 - keep app alive
            print(f"[synth] init failed -> running silent: {exc}")

    # -- ctypes plumbing -----------------------------------------------------

    def _bind(self):
        L = self._lib
        L.new_fluid_settings.restype = ctypes.c_void_p
        L.new_fluid_synth.restype = ctypes.c_void_p
        L.new_fluid_synth.argtypes = [ctypes.c_void_p]
        L.new_fluid_audio_driver.restype = ctypes.c_void_p
        L.new_fluid_audio_driver.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        L.fluid_settings_setstr.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        L.fluid_settings_setint.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        L.fluid_settings_setnum.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_double]
        L.fluid_synth_sfload.restype = ctypes.c_int
        L.fluid_synth_sfload.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        for fn in ("fluid_synth_noteon", "fluid_synth_noteoff",
                   "fluid_synth_program_change", "fluid_synth_cc",
                   "fluid_synth_all_notes_off"):
            getattr(L, fn).argtypes = [ctypes.c_void_p] + [ctypes.c_int] * 3
            getattr(L, fn).restype = ctypes.c_int

    def _start(self, soundfont, audio_driver):
        L = self._lib
        self._settings = L.new_fluid_settings()
        if audio_driver is None:
            audio_driver = os.environ.get("FMTRACKER_AUDIO_DRIVER")
        if audio_driver:
            L.fluid_settings_setstr(self._settings, b"audio.driver", audio_driver.encode())
        L.fluid_settings_setnum(self._settings, b"synth.gain", ctypes.c_double(0.8))
        self._synth = L.new_fluid_synth(self._settings)
        if not self._synth:
            raise RuntimeError("new_fluid_synth returned NULL")
        self._driver = L.new_fluid_audio_driver(self._settings, self._synth)

        soundfont = soundfont or find_default_soundfont()
        if not soundfont:
            raise RuntimeError("no SoundFont found (install fluid-soundfont-gm)")
        self._sfont_id = L.fluid_synth_sfload(self._synth, soundfont.encode(), 1)
        if self._sfont_id == -1:
            raise RuntimeError(f"failed to load SoundFont: {soundfont}")
        self.soundfont = soundfont

    # -- public API ----------------------------------------------------------

    def program_change(self, channel: int, program: int):
        if self.available:
            self._lib.fluid_synth_program_change(self._synth, channel, program, 0)

    def note_on(self, channel: int, key: int, velocity: int = 100):
        if self.available:
            self._lib.fluid_synth_noteon(self._synth, channel, key, velocity)

    def note_off(self, channel: int, key: int):
        if self.available:
            self._lib.fluid_synth_noteoff(self._synth, channel, key, 0)

    def all_notes_off(self, channel: int = -1):
        if not self.available:
            return
        if channel < 0:
            for ch in range(16):
                self._lib.fluid_synth_all_notes_off(self._synth, ch, 0, 0)
        else:
            self._lib.fluid_synth_all_notes_off(self._synth, channel, 0, 0)

    def shutdown(self):
        if not self._lib:
            return
        try:
            if self._driver:
                self._lib.delete_fluid_audio_driver(self._driver)
            if self._synth:
                self._lib.delete_fluid_synth(self._synth)
            if self._settings:
                self._lib.delete_fluid_settings(self._settings)
        except Exception:                            # noqa: BLE001
            pass
        self._driver = self._synth = self._settings = None
        self.available = False
