# Focus DE

Focus DE is a minimal, activity-based Linux desktop (Sway-based) that hosts real
applications inside tabbed, split activities with a pastel / borderless look.

This repository contains the whole desktop as a **payload tree that mirrors `/`**,
plus install tooling — so deploying it is just "extract into `/`".

## Layout

```
FocusDE/
├── rootfs/                     # payload — mirrors / ; extracts straight into the filesystem
│   ├── usr/local/lib/focusde/  #   shared shell code (activities, applets, panel, theme)
│   │   └── apps/fmtracker/     #   the FM-Song Tracker app
│   ├── usr/local/bin/fmtracker #   app launcher
│   ├── etc/skel/.config/       #   default per-user config (sway, waybar, onyx, fuzzel)
│   ├── etc/greetd/config.toml  #   login manager → starts Sway
│   └── usr/share/              #   wayland-sessions + application .desktop entries
├── scripts/                    # install-deps, install, build-archive, remote, songs
└── docs/                       # desktop.md (shell internals)
```

Because the defaults live in **`/etc/skel/.config`**, every user created afterwards
(`adduser …`) automatically gets the Focus DE desktop. The shell code is installed
once, system-wide, under `/usr/local/lib/focusde/`; the Python scripts locate
themselves and read/write per-user data under the real `$HOME`.

## Install

```sh
sudo ./scripts/install-deps.sh           # Sway, waybar, fuzzel, foot, greetd, GTK, fluidsynth…
sudo ./scripts/install.sh --login        # lay payload onto /, seed current user, enable greetd
```

…or build a relocatable archive and unpack it anywhere:

```sh
./scripts/build-archive.sh               # -> focusde-rootfs.tar.gz
sudo tar -C / -xzf focusde-rootfs.tar.gz # extracts every file to its place under /
```

### Login manager (boot straight into the desktop)

The Pi boots into **greetd**, the lightweight login manager for wlroots/Sway. Its
default session (`/etc/greetd/config.toml`) runs `agreety --cmd sway`: a login
prompt that, once authenticated, starts **Sway** — which loads the Focus DE shell.
`install.sh --login` enables it (`systemctl enable greetd`, disabling `getty@tty1`).
A `usr/share/wayland-sessions/focusde.desktop` entry is also provided so any other
display manager can offer "Focus DE". (Install `tuigreet` for a nicer login screen.)

## fmtracker — FM-Song Tracker

A keyboard-and-mouse music tracker, reimagining the author's old QBasic/AdLib
**FM-Song** (and its Onyx/Circle port). Instead of generating sound itself, it
drives a **MIDI** software synthesizer (**fluidsynth**) with a General-MIDI
SoundFont — so it gets hundreds of instruments "for free".

- Multi-pattern song with a looping order-list (the original FM-Song model).
- Up to 16 channels, one GM instrument (program) each.
- **Keyboard** note entry: note letters `C D E F G A B`; `+` / `-` change octave;
  **`Ctrl`+`+` / `Ctrl`+`-`** (or **`Ctrl`+`↑` / `Ctrl`+`↓`**) transpose the cell by a
  semitone; arrows move (up/down = rows/time, left/right = channel/track);
  Space = note-off, Delete = clear.
- **Mouse**: Play / Pause / Resume / Stop, add channel, add pattern, choose
  instrument, set BPM, click a cell to position the cursor.
- Imports legacy `.fms` FM-Song files (instruments default to piano, with a
  name-based heuristic to guess a closer General-MIDI preset).

Run it: `fmtracker` (once installed) or, from a checkout, `./scripts/run.sh`.
Source: [`rootfs/usr/local/lib/focusde/apps/fmtracker/`](rootfs/usr/local/lib/focusde/apps/fmtracker/).
Get the demo songs: [`scripts/install-songs.sh`](scripts/install-songs.sh).

## Remote access (headless Pi)

View/control the Pi's Sway desktop with no monitor via **WayVNC** (headless Sway
output + an SSH tunnel):

```sh
./scripts/setup-remote.sh                 # install wayvnc (one time)
./scripts/sway-headless-vnc.sh 1280x720   # on the Pi: headless Sway + VNC
ssh -L 5900:localhost:5900 <user>@<pi>    # on your machine: tunnel
vncviewer localhost:5900                  # any VNC client
```

See [`docs/desktop.md`](docs/desktop.md) for the shell internals.

> Status: in progress. Written on a Windows dev box; **run/tested on the Linux
> side**. Expect to iterate.
