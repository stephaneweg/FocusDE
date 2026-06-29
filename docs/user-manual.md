# Focus DE — User Manual

Focus DE is a Linux desktop environment **organised around activities** rather than
loose windows. It aims to stay simple and legible (pastel, borderless look), suitable
both for a demo and for a family Raspberry Pi.

> The on-screen interface is in French; this manual keeps the real button labels
> (e.g. **Accueil** = *Home*, **Créer** = *Create*) and explains them in English.

---

## 1. The concept

Instead of stacking windows on a desktop, Focus DE groups what you do into
**activities**. An activity is a context (a project, a game, a work session…) that
fills the screen and is split into **zones**. When you step back, you return to the
**Accueil** (Home): the overview of your activities.

It is inspired by the *Sugar* desktop (OLPC): you "zoom" between the overview (Home)
and a single activity.

Three ideas are enough to understand everything:

- **Activity** — a full-screen space dedicated to one task (a Sway *workspace*).
- **Zone** — an activity is divided into a *primary screen* (top), a *secondary
  screen* (bottom) and a *panel* on the left.
- **Applet** — a small utility tile (clock, notes…) placed in the panel.

---

## 2. The desktop at a glance

![Focus DE Home](images/home.png)

A discreet **bar** sits at the top:

| Element | Role |
|--------|------|
| *(left)* activity name | the current activity |
| **+ App** | add an application (opens the picker) |
| **Panneau** | show / hide the applet panel |
| **Accueil** | go back to the overview |
| *(right)* clock | the time |

---

## 3. Accueil — the Home

The Home is your starting point (click **Accueil** in the bar at any time). It shows:

- a personalised **greeting** and the date;
- status **cards** (*Reprendre* = Resume, *En ce moment* = Now playing, *Aujourd'hui*
  = Today);
- the **hub tiles** (*Travailler, Apprendre, Jouer, Naviguer, Créer*) — see §7;
- your open **activities** (one coloured tile each);
- the **+ Nouvelle activité** (New activity) tile;
- on the left, the **applet panel** (by default: Clock + Notes).

---

## 4. Activities

**Create an activity**: click the **+ Nouvelle activité** tile and give it a name. It
opens empty, ready to be filled with applications.

**Switch activities**: click its tile from the Home. (Under the hood each activity is
a Sway workspace; `Super`+`1`…`9` also works.)

---

## 5. Zones: primary, secondary and panel

![An activity with two zones (top/bottom) and the panel](images/activity-zones.png)

An activity has three zones:

- **Primary screen** (top) — the main work area;
- **Secondary screen** (bottom) — a second area, e.g. a terminal or notes;
- **Panel** (left) — holds the applets and the **+** button.

When a zone holds several applications, they line up as **tabs** (the coloured bars
at the top of a zone).

**Maximise a zone** (temporary full screen):

- `Super`+`Page Up` → maximise the **primary** screen;
- `Super`+`Page Down` → maximise the **secondary** screen.

---

## 6. Adding an application

![The application picker (+ App)](images/picker.png)

Click **+ App** in the bar (or press `Super`+`T`). The picker opens:

1. Choose **where** to add it: **En haut** (primary), **En bas** (secondary), or
   **Raccourci (hub)** to pin it into a hub (§7).
2. Search/click the application — the list contains **every** application installed
   on the system.

The application opens in the chosen zone (as a tab if the zone is already occupied).

---

## 7. Hubs (application categories)

![The "Créer" (Create) hub](images/hub-creer.png)

From the Home, the **Travailler / Apprendre / Jouer / Naviguer / Créer** tiles open a
**hub**: a grid of applications for that category, filled automatically from the
standard *freedesktop* categories:

| Hub | Contents |
|-----|----------|
| **Travailler** (Work) | office apps (word processor, spreadsheet, finance…) |
| **Apprendre** (Learn) | educational software |
| **Jouer** (Play) | games |
| **Naviguer** (Browse) | the web browser |
| **Créer** (Create) | **creation** tools — graphics **and** audio/music |

> The **Créer** hub distinguishes *creation* from *consumption*: it lists editors
> (drawing, image editing, audio trackers…) and **excludes** plain image/document
> viewers and media players.

You can also **pin** any application into a hub from the picker (**+ App** → the
**Raccourci (hub)** zone).

---

## 8. Applets (left panel)

![The applet manager](images/applets.png)

The left panel hosts **applets**. Click the **+** at the top of the panel
("Applets") to choose which ones to show, then **Appliquer** (Apply).

| Applet | Description | Usage |
|--------|-------------|-------|
| **Horloge** (Clock) | Time and date | simple display |
| **Notes** | Activity notes (or *everywhere* from the Home) | **+ Nouvelle** to add; the **eye** shows a note, the **trash** deletes it |
| **Calculatrice** (Calculator) | Quick sums | calculations without leaving the activity |
| **Musique** (Music) | Plays files from `~/Music` | listen to your music (MP3/OGG/FLAC…) |
| **FM-Player** | Plays FM-Song `.fms` tunes | a single file or a whole folder — see below |
| **Rappel** (Reminder) | Upcoming agenda events | a glance at your agenda |

The **Panneau** button in the bar shows/hides the panel.

### The FM-Player applet

![The FM-Player applet in the panel](images/applet-fmplayer.png)

FM-Player plays **FM-Song `.fms`** tunes right in the panel, using the FM-Song
Tracker engine (fluidsynth + a General-MIDI SoundFont):

- **Dossier** (Folder) loads a whole folder as a playlist; **Fichier** (File) loads a
  single tune. By default it scans `~/fms` (then `~/Music`).
- Transport: previous / **play–pause** / stop / next. Click a tune in the list to
  play it; the player auto-advances to the next when one finishes.

---

## 9. Built-in software

### FM-Song Tracker

![FM-Song Tracker with a tune loaded](images/fmtracker.png)

**FM-Song Tracker** is a music *tracker*: you compose by placing notes in a grid. The
sound is produced by a **MIDI** synthesizer (fluidsynth) with a *General MIDI*
instrument bank — hundreds of instruments available. It also imports the original
FM-Song **`.fms`** tunes.

**Launch**: from the **Créer** hub, via **+ App**, or on the command line
`fmtracker my_tune.fms`. The **Open .fms** button opens an existing tune.

**Reading the grid**: each **column** is a channel (an instrument); each **row** is a
step (time runs downward).

- `----` : empty cell (the previous note keeps sounding);
- `===` : a rest (the note stops);
- `C-5`, `F#4`… : a note.

**Keyboard entry**:

| Key | Action |
|-----|--------|
| `C D E F G A B` | enter that note |
| `+` / `-` | move up / down an **octave** |
| `Ctrl`+`+` / `Ctrl`+`-` (or `Ctrl`+`↑`/`↓`) | transpose the cell by a **semitone** |
| `↑ ↓` | move the cursor through time |
| `← →` | change **channel** |
| `Space` | insert a **rest** |
| `Delete` | clear the cell |

**Mouse (toolbar)**: **▶ Play**, **❚❚ Pause**, **Resume**, **■ Stop**; **+ Channel** /
**+ Pattern**; the **BPM**; the **Pattern** selector; and the **Instrument**
(General-MIDI preset) of the current channel.

During playback the grid **scrolls** to follow the play-head and **chains patterns**
according to the order list, looping.

**Exporting your music** — the **Export ▾** button writes the song as:

| Format | Notes |
|--------|-------|
| **MIDI** (`.mid`) | written natively from the song |
| **WAV** (`.wav`) | rendered through fluidsynth + the SoundFont |
| **MP3** (`.mp3`) | re-encoded with `ffmpeg` |
| **MuseScore** (`.mscz`) | converted with the `mscore` CLI — the `.mid` also opens directly in MuseScore |

> FM-Song Tracker descends from **FM-Song** by *Asher256*, a QuickBASIC AdLib/OPL
> tracker ([github.com/Asher256](https://github.com/Asher256) ·
> [qbworld.asher256.com](https://qbworld.asher256.com/)). This is a modern
> reimagining (MIDI / fluidsynth) that still opens the original `.fms` tunes.

---

## 10. Themes

![Choosing a theme](images/theme-picker.png)

Press `Super`+`Shift`+`T` to open **Choisir un thème** (Choose a theme). Pick from a
palette of light and dark themes (Lavande, Océan, Forêt, Nuit, Encre…); the change
is applied **live**.

The **Partout** / **Cette activité** toggle sets the scope:

- **Partout** (Everywhere) — the default theme for the whole desktop;
- **Cette activité** (This activity) — a colour just for the current activity, so
  each activity can look distinct.

---

## 11. Keyboard shortcuts

`Super` = the logo key (Windows / ⌘).

| Shortcut | Action |
|----------|--------|
| `Super`+`T` | **+ App** (application picker) |
| `Super`+`Shift`+`T` | change the **theme** |
| `Super`+`Page Up` / `Page Down` | maximise the **primary** / **secondary** screen |
| `Super`+`Enter` | open a **terminal** |
| `Super`+`D` | application menu (fuzzel) |
| `Super`+`arrows` | change the focused window |
| `Super`+`Shift`+`arrows` | move the window |
| `Super`+`1`…`9` | go to an activity |
| `Super`+`Shift`+`Q` | close the window |
| `Super`+`Shift`+`C` | reload Focus DE (Sway) |

---

See also: [installation](install.md) · [project overview](../README.md).
