"""General MIDI program names and a name-based heuristic for legacy instruments."""

from __future__ import annotations

GM_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano",
    "Honky-tonk Piano", "Electric Piano 1", "Electric Piano 2", "Harpsichord",
    "Clavi", "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
    "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ",
    "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ",
    "Accordion", "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)",
    "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
    "Distortion Guitar", "Guitar harmonics", "Acoustic Bass",
    "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin",
    "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings",
    "Orchestral Harp", "Timpani", "String Ensemble 1", "String Ensemble 2",
    "SynthStrings 1", "SynthStrings 2", "Choir Aahs", "Voice Oohs",
    "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone", "Tuba",
    "Muted Trumpet", "French Horn", "Brass Section", "SynthBrass 1",
    "SynthBrass 2", "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
    "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute",
    "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle",
    "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)",
    "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)",
    "Lead 8 (bass + lead)", "Pad 1 (new age)", "Pad 2 (warm)",
    "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)",
    "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)",
    "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)",
    "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo",
    "Shamisen", "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum",
    "Melodic Tom", "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise",
    "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter",
    "Applause", "Gunshot",
]

# Ordered (substring -> GM program). First match wins; checked case-insensitively.
_HEURISTIC = [
    ("piano", 0), ("epiano", 4), ("rhodes", 4), ("clav", 7), ("harpsi", 6),
    ("vibe", 11), ("vibr", 11), ("marimba", 12), ("xylo", 13), ("bell", 14),
    ("organ", 16), ("accord", 21), ("harmonica", 22),
    ("nylon", 24), ("guitar", 27), ("gtr", 27), ("dist", 30),
    ("bass", 33), ("violin", 40), ("viola", 41), ("cello", 42),
    ("string", 48), ("strings", 48), ("choir", 52), ("voice", 53),
    ("trumpet", 56), ("tromb", 57), ("tuba", 58), ("horn", 60),
    ("brass", 61), ("sax", 65), ("oboe", 68), ("clarinet", 71),
    ("flute", 73), ("pan", 75), ("whistle", 78), ("ocarina", 79),
    ("square", 80), ("saw", 81), ("lead", 80), ("pad", 88),
    ("sitar", 104), ("banjo", 105), ("steel", 114), ("drum", 118),
    ("perc", 115), ("snare", 118), ("kick", 118),
]


def guess_program(name: str) -> int:
    """Best-effort GM program from a legacy instrument name. Defaults to 0 (piano)."""
    if not name:
        return 0
    n = name.strip().lower()
    for needle, prog in _HEURISTIC:
        if needle in n:
            return prog
    return 0
