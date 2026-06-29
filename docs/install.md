# Focus DE — Installation

Focus DE installs **once** on the machine and becomes the default desktop for **all**
users (including users created later).

## Requirements

- A **Debian / Ubuntu / Raspberry Pi OS** system (tested on a Raspberry Pi 4, arm64).
  The package is architecture-independent (`all`).
- **root** access (`sudo`) and an internet connection (for dependencies).

Dependencies are pulled automatically: Sway, waybar, fuzzel, foot, greetd, Python 3 +
PyGObject (GTK 3 and 4) + Cairo, fluidsynth + a General-MIDI SoundFont, plus AbiWord,
Gnumeric and Firefox for the hosted applications.

## Install

### Option A — Debian package (recommended)

```sh
sudo apt install ./focusde_0.1.0_all.deb
```

`apt` installs Focus DE **and** all its dependencies. To build the package from
source:

```sh
./scripts/build-deb.sh 0.1.0       # -> focusde_0.1.0_all.deb
```

### Option B — from source

```sh
git clone https://github.com/stephaneweg/FocusDE
cd FocusDE
sudo ./scripts/install-deps.sh     # prerequisites (Sway, GTK, fluidsynth…)
sudo ./scripts/install.sh --login  # install Focus DE + enable the login screen
```

`install.sh` lays the desktop onto the system and installs it for the current user.
You can also extract a ready-made archive:

```sh
./scripts/build-archive.sh                 # -> focusde-rootfs.tar.gz
sudo tar -C / -xzf focusde-rootfs.tar.gz   # every file goes to its place
```

## First boot

With `--login`, the machine boots into **greetd**, the login screen: enter your
username and the **Focus DE (Sway)** session starts.

Without a login manager, open a console and simply run:

```sh
sway
```

## New users

The default configuration lives in `/etc/skel/.config`. Any account created
afterwards therefore gets Focus DE **automatically**:

```sh
sudo adduser kid     # "kid" gets the Focus DE desktop on first login
```

To apply Focus DE to an **existing** user:

```sh
cp -a /etc/skel/.config/. ~/.config/
```

## Headless Raspberry Pi (remote access)

To drive the desktop of a Pi with no monitor, see
[`scripts/setup-remote.sh`](../scripts/setup-remote.sh): it installs **WayVNC**
(headless Sway + an SSH tunnel) so you can view and control the session.

## Where files are installed

| Location | Contents |
|----------|----------|
| `/usr/local/lib/focusde/` | the shell code (+ `apps/fmtracker/`) |
| `/usr/local/bin/fmtracker` | the tracker launcher |
| `/etc/skel/.config/` | default configuration (sway, waybar, focus, fuzzel) |
| `/etc/greetd/config.toml` | the login screen |
| `/usr/share/wayland-sessions/focusde.desktop` | session offered to login managers |

## Uninstall

```sh
sudo apt remove focusde     # if installed from the .deb
```

---

See also: [user manual](user-manual.md) · [project overview](../README.md).
