# Focus DE — desktop shell

The Focus DE activity shell that runs on top of **Sway** (wlroots) on the
Raspberry Pi: pastel/borderless look, activities (tabbed splits = the Sway tree),
a home/hub launcher, applets, and a theme system.

This is a snapshot of the working shell. Personal runtime data (notes, agenda
contents) is intentionally **not** included.

## Where it lives (payload tree)

Everything ships in `rootfs/`, which mirrors `/`:

| Repo path | Installs to | Role |
|-----------|-------------|------|
| `rootfs/usr/local/lib/focusde/`        | same | shared **code** (Python + shell logic), read-only |
| `rootfs/usr/local/lib/focusde/apps/`   | same | hosted apps (fmtracker) |
| `rootfs/etc/skel/.config/`             | `/etc/skel/.config/` → each user's `~/.config/` | per-user **config** (sway, waybar, onyx, fuzzel) |
| `rootfs/etc/greetd/config.toml`        | same | login manager → Sway |

The Python scripts locate themselves (`os.path.realpath(__file__)`), so the code
is relocatable; per-user data (notes, agenda, chosen theme) is read/written under
the real `$HOME`. The config references the code by its install path
(`/usr/local/lib/focusde/`) and per-user button scripts via `$HOME`. Because the
defaults live in `/etc/skel/.config`, every user created afterwards automatically
gets the desktop. See the top-level [README](../README.md) for install commands.

## Components

(paths below are under `rootfs/usr/local/lib/focusde/` for code and
`rootfs/etc/skel/.config/` for config)

**Sway** — `…/.config/sway/config`: pastel palette, fine borders, tabbed vertical
layout, keybinds that launch the Python tools below.

**Activities / workspaces** — `activity.py`, `activity_switcher.py`,
`zone_max.py`; `act.json` is the default window layout for a new activity.

**Home / launcher** — `home.py`, `hub.py`, `picker.py` (`$mod+t`); activity
collections in `…/.config/onyx/hubs/*.list`; `…/.config/fuzzel/fuzzel.ini`.

**Applets** — framework: `applet.py`, `applet_mgr.py`, `onyx_applets.py`,
`panel_host.py`, `panel_toggle.py`; applets: `applet_clock.py`, `applet_calc.py`,
`applet_music.py`, `applet_notes.py`, `applet_rappel.py`; per-activity layout in
`…/.config/onyx/applets/*`.

**Theme** — `theme.py`, `theme_apply.py`, `theme_daemon.py`, `onyx_theme.py`
(`$mod+Shift+t`); definitions in `…/.config/onyx/{theme,themes/{Vert,Bleu}}`.

**Agenda / notes** — `agenda.py`, `event_dialog.py`, `note_dialog.py`.

**Panel (waybar)** — `…/.config/waybar/{config.jsonc,style.css}` and the
`{home,add,applet,panel,activity-name}-btn.sh` buttons.

**Boot / helpers** — `focus_boot.sh` (session boot), `go_home.sh`, `add_app.sh`,
`setup_autostart.sh` (a no-display-manager fallback that execs Sway on tty1).

> The `fmtracker` app
> ([`rootfs/usr/local/lib/focusde/apps/fmtracker/`](../rootfs/usr/local/lib/focusde/apps/fmtracker/))
> is one of the applications hosted inside these activities.
