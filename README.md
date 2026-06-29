# Focus DE

Focus DE is a minimal, activity-based Linux desktop (Sway-based) that hosts real
applications inside tabbed, split activities with a pastel / borderless look.

This repository collects the Focus DE applications and the installation tooling.

## Layout

```
FocusDE/
├── app/                 # the applications
│   └── fmtracker/       # FM-Song Tracker — a MIDI tracker (fluidsynth-backed)
└── scripts/             # install / setup scripts (apt prerequisites, launchers)
```

The long-term goal is that an end user can install Focus DE and all of its
prerequisites with either:

- `git clone … && ./scripts/install.sh`, or
- a `.deb` / `apt` package.

## fmtracker — FM-Song Tracker

A keyboard-and-mouse music tracker, reimagining the author's old QBasic/AdLib
**FM-Song** (and its Onyx/Circle port). Instead of generating sound itself, it
drives a **MIDI** software synthesizer (**fluidsynth**) with a General-MIDI
SoundFont — so it gets hundreds of instruments "for free".

Highlights:

- Multi-pattern song with a looping order-list (the original FM-Song model).
- Up to 16 channels, one GM instrument (program) each.
- **Keyboard** note entry: note letters `C D E F G A B`, `#` / `b` accidentals,
  `+` / `-` to change octave, arrows to move (up/down = rows/time,
  left/right = channel/track), Space = note-off, Delete = clear.
- **Mouse** for everything else: Play / Pause / Resume / Stop, add channel,
  add pattern, choose instrument, set BPM, click a cell to position the cursor.
- Imports legacy `.fms` FM-Song files (instruments default to piano, with a
  name-based heuristic to guess a closer General-MIDI preset).

See [`app/fmtracker/`](app/fmtracker/) and [`scripts/`](scripts/).

### Quick start (Linux)

```sh
./scripts/install-deps.sh      # apt prerequisites (GTK4, PyGObject, fluidsynth, GM soundfont)
./scripts/run.sh               # launch the tracker
```

> Status: first scaffold. Written on a Windows dev box; **run/tested on the Linux
> side**. Expect to iterate.
