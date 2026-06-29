# Focus DE — desktop shell

The Focus DE activity shell that runs on top of **Sway** (wlroots) on the
Raspberry Pi: pastel/borderless look, activities (tabbed splits = the Sway tree),
a home/hub launcher, applets, and a theme system.

This is a snapshot of the working tree as it lives on the Pi. Personal runtime
data (notes, agenda contents) is intentionally **not** included.

## Deploy mapping

The two subfolders mirror where the files live on the Pi:

| Repo | On the Pi |
|------|-----------|
| `desktop/home/`   | `~` (i.e. `/home/maison/`) |
| `desktop/config/` | `~/.config/` |

```sh
# from this folder, on the Pi (or over rsync from a checkout):
rsync -a home/   /home/maison/
rsync -a config/ /home/maison/.config/
```

## What's here

**Sway**
- `config/sway/config` — the Sway config: pastel palette, fine borders, tabbed
  vertical layout, keybinds that launch the Python tools below.

**Activities / workspaces**
- `home/activity.py`, `home/activity_switcher.py` — activity model & switching.
- `home/zone_max.py` — maximize / zone handling.
- `home/act.json` — default window layout for a new activity.

**Home / launcher**
- `home/home.py`, `home/hub.py`, `home/picker.py` — home screen + app picker
  (`$mod+t`). Activity collections in `config/onyx/hubs/*.list`.
- `config/fuzzel/fuzzel.ini` — fuzzel launcher styling.

**Applets**
- `home/applet.py`, `home/applet_mgr.py`, `home/onyx_applets.py`,
  `home/panel_host.py`, `home/panel_toggle.py` — applet framework + panel host.
- `home/applet_clock.py`, `applet_calc.py`, `applet_music.py`,
  `applet_notes.py`, `applet_rappel.py` — the individual applets.
- Per-activity applet layout in `config/onyx/applets/*`.

**Theme**
- `home/theme.py`, `home/theme_apply.py`, `home/theme_daemon.py`,
  `home/onyx_theme.py` (`$mod+Shift+t`) — theme picker / live apply.
- `config/onyx/theme`, `config/onyx/themes/{Vert,Bleu}` — theme definitions.

**Agenda / notes**
- `home/agenda.py`, `home/event_dialog.py`, `home/note_dialog.py`.

**Panel (waybar)**
- `config/waybar/config.jsonc`, `style.css` — the bar.
- `config/waybar/{home,add,applet,panel,activity-name}-btn.sh` — bar buttons.

**Boot / helpers**
- `home/focus_boot.sh` — session boot.
- `home/go_home.sh`, `home/add_app.sh`, `home/setup_autostart.sh`.

> The `fmtracker` app (see [`../app/fmtracker/`](../app/fmtracker/)) is one of the
> applications hosted inside these activities.
