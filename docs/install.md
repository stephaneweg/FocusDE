# Focus DE — Installation

Focus DE s'installe **une fois** sur la machine et devient le bureau par défaut de
**tous** les utilisateurs (y compris ceux créés ensuite).

## Prérequis

- Une distribution **Debian / Ubuntu / Raspberry Pi OS** (testé sur Raspberry Pi 4,
  arm64). Le paquet est *architecture-indépendante* (`all`).
- Un accès **root** (`sudo`) et une connexion internet (pour les dépendances).

Les dépendances sont tirées automatiquement : Sway, waybar, fuzzel, foot, greetd,
Python 3 + PyGObject (GTK 3 et 4) + Cairo, fluidsynth + une SoundFont General MIDI,
ainsi que AbiWord, Gnumeric et Firefox pour les applications hébergées.

## Installer

### Option A — paquet Debian (recommandé)

```sh
sudo apt install ./focusde_0.1.0_all.deb
```

`apt` installe Focus DE **et** toutes ses dépendances. Pour fabriquer le paquet
depuis les sources :

```sh
./scripts/build-deb.sh 0.1.0       # -> focusde_0.1.0_all.deb
```

### Option B — depuis les sources

```sh
git clone https://github.com/stephaneweg/FocusDE
cd FocusDE
sudo ./scripts/install-deps.sh     # les prérequis (Sway, GTK, fluidsynth…)
sudo ./scripts/install.sh --login  # installe Focus DE + active l'écran de connexion
```

`install.sh` dépose le bureau sur le système et l'installe pour l'utilisateur courant.
On peut aussi extraire une archive prête à l'emploi :

```sh
./scripts/build-archive.sh                 # -> focusde-rootfs.tar.gz
sudo tar -C / -xzf focusde-rootfs.tar.gz   # chaque fichier va à sa place
```

## Premier démarrage

Avec l'option `--login`, la machine démarre sur **greetd**, l'écran de connexion :
saisissez votre identifiant, et la session **Focus DE (Sway)** se lance.

Sans gestionnaire de connexion, ouvrez une console et lancez simplement :

```sh
sway
```

## Nouveaux utilisateurs

La configuration par défaut vit dans `/etc/skel/.config`. Tout compte créé ensuite
récupère donc **automatiquement** Focus DE :

```sh
sudo adduser enfant     # « enfant » obtient le bureau Focus DE au premier login
```

Pour appliquer Focus DE à un utilisateur **déjà existant** :

```sh
cp -a /etc/skel/.config/. ~/.config/
```

## Raspberry Pi sans écran (accès distant)

Pour piloter le bureau d'un Pi sans moniteur, voir
[`scripts/setup-remote.sh`](../scripts/setup-remote.sh) : il installe **WayVNC**
(Sway en mode *headless* + un tunnel SSH) afin de voir et contrôler la session.

## Où les fichiers sont installés

| Emplacement | Contenu |
|-------------|---------|
| `/usr/local/lib/focusde/` | le code du shell (+ `apps/fmtracker/`) |
| `/usr/local/bin/fmtracker` | lanceur du tracker |
| `/etc/skel/.config/` | configuration par défaut (sway, waybar, onyx, fuzzel) |
| `/etc/greetd/config.toml` | écran de connexion |
| `/usr/share/wayland-sessions/focusde.desktop` | session proposée aux gestionnaires de connexion |

## Désinstaller

```sh
sudo apt remove focusde     # si installé via le .deb
```

---

Voir aussi : [manuel d'utilisation](user-manual.md) · [présentation](../README.md).
