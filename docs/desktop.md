# Focus DE — desktop shell (internals)

The Focus DE activity shell runs on top of **Sway** (wlroots) on the Raspberry Pi:
pastel, borderless, full-screen look; activities (split + tabbed = the Sway tree); a
home/hub launcher; applets; and a live theme system. The whole UI is **Sway driven by
small Python/GTK tools**, wired to the top **waybar** buttons and a few keybinds.

This is a snapshot of the working shell. Personal runtime data (notes, agenda
contents) is intentionally **not** included.

## Where it lives (payload tree)

Everything ships in `rootfs/`, which mirrors `/`:

| Repo path | Installs to | Role |
|-----------|-------------|------|
| `rootfs/usr/local/lib/focusde/`        | same | shared **code** (Python + shell logic), read-only |
| `rootfs/usr/local/lib/focusde/apps/`   | same | hosted apps (fmtracker) |
| `rootfs/etc/skel/.config/`             | `/etc/skel/.config/` → each user's `~/.config/` | per-user **config** (sway, waybar, focus, fuzzel) |
| `rootfs/etc/greetd/config.toml`        | same | login manager → Sway |

The Python scripts locate themselves (`os.path.realpath(__file__)`), so the code is
relocatable; per-user data (notes, agenda, chosen theme, applet selection) is
read/written under the real `$HOME` (`~/.config/focus/…`). The config references the
code by its install path (`/usr/local/lib/focusde/`) and the per-user button scripts
via `$HOME`. Because the defaults live in `/etc/skel/.config`, every user created
afterwards automatically gets the desktop. See the [README](../README.md) for install
commands.

## Activities, workspaces and zones

**An activity = a named Sway workspace.** Workspaces are **created on the fly** (nothing
is pre-declared at boot except *Accueil*): a tool switches to a free workspace number
and `rename`s it to the activity name. Sway destroys a workspace as soon as its last
window closes, so "stopping" an activity is just closing its windows.

Inside an activity the layout is **horizontal** (`default_orientation horizontal`,
`gaps 0` for the full-screen look). Three logical **zones**, identified by **marks** on
the window that anchors each zone:

| Zone | Mark | Position | Container |
|------|------|----------|-----------|
| Primary  | `Zp_<wsid>` | left, ~2/3 width | tabbed |
| Secondary | `Zs_<wsid>` | right, ~1/3 width | tabbed |
| Panel (applets) | `Zl_<wsid>` | far left column | splitv (stacked applets) |

`<wsid>` is the Sway **container id** of the workspace at build time; all per-activity
data is keyed by a `slug(name)` instead (so it survives id changes) — see *Data*.

### Placing a window (`activity.py`)

`add(zone, cmd)` launches the command, captures the new window via a one-shot
`get-tree`/window-event subscription (`launch_get`), then either moves it into the
existing zone (`move container to mark Z*_<wsid>`) or builds the zone with
`recreate_zone`. Two layout subtleties are handled explicitly:

- **Popping a window out of a tabbed container** is *vertical*: in a tabbed container
  left/right reorder tabs, so a window only exits by moving up/down. To create the
  side-by-side primary/secondary, the new window is moved *down* out of the neighbour's
  tabs and the shared container is then flipped to `splith`; secondary is resized to
  `33 ppt` (1/3), primary to `67 ppt` (2/3).
- **The applet panel** must become the left **column**, not a tab. `pop_left(selector)`
  moves the container left until it is a **direct child of the workspace** (instead of
  a fixed number of `move left`, which fails as soon as the content zone has more than
  one tab).

### The scratchpad: folding panel and secondary

Both the panel and the secondary zone are *hidden* by sending their container to the
Sway **scratchpad** (true hide, not a resize):

- `panel_toggle.py` (**Panneau** button) folds/unfolds the `Zl` panel; on show it
  re-docks it as the left column (`pop_left` + `split vertical` + width 240px).
- `secondary_toggle.py` (**Secondaire** button) folds/unfolds the whole `Zs` container;
  on show it re-docks it on the right (move-down + flip `splith` + `33 ppt`). The button
  appears only when a `Zs_<wsid>` mark exists for the focused workspace.

### Maximise / restore a zone

`zone_max.py` (`$mod+PageUp` / `$mod+PageDown`) toggles the split between **2/3-1/3** and
near-full, by **width** (left/right), reading the live `Zp`/`Zs` rectangles.

### Building & cleaning the Home

`build_home()` (`activity.py home`, run by `focus_boot.sh`) builds *Accueil* (panel +
`home.py`) idempotently. It calls `reap_stale_panels(wsid)` in **both** paths — the
"already built" shortcut *and* after a fresh build — to kill any orphan `focus-panel`
left over from an earlier boot rebuild (a panel whose mark doesn't match the current
workspace id), which otherwise stacked a duplicate panel on the Home.

### Stopping an activity

`activity.py stop [<ws>]` (**✕** button → `stop_activity.py` confirmation dialog) kills
every window of the workspace; Sway then recycles the now-empty workspace and the tool
switches back to *Accueil*. `record_activity()` is a deliberate **no-op hook** left in
`stop()` — the future write point for activity **persistence** (so a stopped activity
can reappear on the Home next to the hubs and be relaunched). Not yet wired.

## Components

(paths below are under `rootfs/usr/local/lib/focusde/` for code and
`rootfs/etc/skel/.config/` for config)

**Sway** — `…/.config/sway/config`: pastel palette, fine borders, `gaps 0`,
`default_orientation horizontal`, and the keybinds that launch the Python tools.

**Activities / zones** — `activity.py` (build/add/stop/reap, the zone engine),
`activity_switcher.py` (the title-bar switcher), `panel_toggle.py`,
`secondary_toggle.py`, `zone_max.py`; `act.json` is a reference layout.

**Home / launcher** — `home.py` (the Home app: greeting, cards, hub + activity tiles),
`hub.py` (a category grid), `picker.py` (`$mod+t`; choose zone **Principal /
Secondaire / Raccourci** then app); hub contents in `…/.config/focus/hubs/*.list`;
fuzzel in `…/.config/fuzzel/fuzzel.ini`.

**Applets** — framework: `applet.py`, `applet_mgr.py`, `focus_applets.py`,
`panel_host.py` (the GTK host that stacks the chosen applets); applets:
`applet_clock.py`, `applet_calc.py`, `applet_music.py`, `applet_notes.py`,
`applet_rappel.py`, `applet_fmplayer.py` (plays `.fms` via the fmtracker engine).
Per-activity applet selection in `…/.config/focus/applets/<slug>`.

**Theme** — `focus_theme.py` (palette loader + helpers), `theme.py` (the picker,
`$mod+Shift+t`), `theme_apply.py`, `theme_daemon.py` (subscribes to Sway `workspace`
events and re-applies the **per-activity** palette to Sway + waybar on each switch,
without a restart). Palettes are **data**: `focus_theme` loads them from
`themes.json` (system: next to the code; user: `~/.config/focus/themes.json`, which
overlays the system file), keyed by colour name, with the hard-coded `_DEFAULT_PALETTES`
only as a fallback — so themes can be added/edited without touching the code. The
chosen theme(s) are stored in `…/.config/focus/{theme,themes/<slug>}`. The doc palette
strips come from [`tools/gen_palettes.py`](../tools/gen_palettes.py), which reads the
same definitions.

**Agenda / notes** — `agenda.py` (floating agenda window), `event_dialog.py`,
`note_dialog.py`; data in `…/.config/focus/{agenda.json,notes/<scope>.json}`.

**Assistant (Professeur Neuro)** — `neuro.py`: a lightweight GTK3 chat that streams from
an **OpenAI-compatible** API (default **Groq**, `llama-3.3-70b-versatile`) configured in
`~/.config/focus/assistant/config.json` (`base_url`/`model`/`api_key`, chmod 600). It keeps
a **per-activity history** (`assistant/<slug>.json`), shows a large **mood avatar** driven by
a `[humeur:X]` tag the model emits (parsed then stripped; images in `assistant/moods/*.png`),
reads replies aloud with **Piper** (offline TTS, sentence-by-sentence in step with the text;
🔊/🔇 toggle persisted in the config), and **adapts to age** — the child's **birthdate** is
stored globally in `~/.config/focus/user.json` (asked on first run, or parsed from "j'ai X
ans"), recomputed each turn and injected into the prompt along with the current activity
title. `neuro_search.py` is an optional **RAG** step (web via Tavily + academic via OpenAlex,
Wikipedia excluded; off unless `"search": true`) and also forces **IPv4-first** name
resolution for the whole process (a broken IPv6 path otherwise stalls the API calls ~60 s).
The persona lives in `assistant/professeur-neuro.json`. `assistant_toggle.py` (the bar
button) tracks the assistant **per activity** via a `Zasst_<wsid>` mark and runs it as a **tab
of the secondary zone** (`add secondary`): visible → kill the tab (secondary folds if it was
alone); folded → reveal; absent → add + mark.

**Panel (waybar)** — `…/.config/waybar/{config.jsonc,style.css}` and the per-user
button scripts: `activity-name.sh` (title + switcher), `add-btn.sh` (**+ App**),
`assistant-btn.sh` (**🦉 Neuro** — an **image** module: the script prints the avatar image
path, empty on the Home to hide it), `panel-btn.sh` (**Panneau**), `secondary-btn.sh`
(**Secondaire**, shown only when a secondary zone exists), `home-btn.sh` (**Accueil**),
`stop-btn.sh` (**✕**, red, shown only inside an activity). The waybar style is also produced
from `focus_theme.WAYBAR_STYLE` when the theme changes (so button styles survive a theme
switch).

**Boot / helpers** — `focus_boot.sh` (session boot: wait for Sway, build the Home,
retry-safe), `go_home.sh`, `add_app.sh`, `setup_autostart.sh` (a no-display-manager
fallback that execs Sway on tty1).

## Data (per user, under `~/.config/focus/`)

| Path | Contents |
|------|----------|
| `theme`, `themes/<slug>` | global theme, per-activity theme |
| `applets/<slug>` | applet selection for an activity |
| `notes/<scope>.json` | notes (`__global__` or per-activity slug) |
| `agenda.json` | agenda events (shared by the Agenda and the Rappel applet) |
| `hubs/<slug>.list` | apps pinned into a hub |
| `name` | display name used in the Home greeting |
| `user.json` | global user profile (birthdate → the assistant's age adaptation) |
| `assistant/<slug>.json`, `assistant/config.json` | per-activity chat history; assistant API/voice config |

All keyed by `slug(activity_name)`, so panel/notes/theme stay aligned across an
activity's lifetime regardless of its Sway workspace id.

## The fmtracker app & engine

[`apps/fmtracker/`](../rootfs/usr/local/lib/focusde/apps/fmtracker/) is a hosted
application **and** a reusable, GTK-free engine:

- engine: `model.py`, `fms.py` (legacy `.fms` import), `synth.py` (libfluidsynth via
  ctypes), `sequencer.py`, `gm.py` (General-MIDI names), `export.py`
  (MIDI/WAV/MP3 + native MuseScore `.mscx`) and MIDI import;
- UI: `gridview.py` + `app.py` (GTK4), launched by `/usr/local/bin/fmtracker`.

The **FM-Player** applet reuses that engine from the GTK3 shell to play `.fms` tunes in
the panel.
