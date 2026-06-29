# Focus DE

> Un bureau Linux **par activités**, pas par fenêtres. Clair, pastel, sans bordures —
> conçu pour se concentrer, et idéal pour un Raspberry Pi familial.

![L'Accueil de Focus DE](docs/images/home.png)

Focus DE remplace le « tas de fenêtres » habituel par des **activités** : chaque
projet occupe tout l'écran, se découpe en zones nettes, et l'**Accueil** vous donne
la vue d'ensemble. Le tout sur **Sway** (Wayland), avec de **vraies** applications
Linux hébergées dedans.

## Pourquoi Focus DE

- 🎯 **Une chose à la fois.** Une activité = un contexte plein écran. Fini les
  trente fenêtres éparpillées.
- 🧩 **Des zones simples.** Écran principal, écran secondaire, panneau d'applets —
  et des onglets quand une zone reçoit plusieurs apps.
- 🗂️ **Des hubs thématiques.** *Travailler, Apprendre, Jouer, Naviguer, Créer* :
  vos applications rangées par usage, automatiquement.
- 🔌 **Des applets utiles.** Horloge, Notes, Calculatrice, Musique, Rappels — dans
  le panneau, à portée de main.
- 🎹 **Des logiciels intégrés.** Dont **FM-Song Tracker**, un tracker de musique MIDI.
- 🍓 **Léger.** Pensé pour le Raspberry Pi 4 ; s'installe pour **tous** les
  utilisateurs en une fois.

## Le concept en 30 secondes

| | |
|---|---|
| ![Hub Créer](docs/images/hub-creer.png) | **Des hubs** regroupent vos apps par usage. « Créer » réunit les outils de création (dessin, audio…) — et écarte les simples visionneuses. |
| ![Zones](docs/images/activity-zones.png) | **Une activité, deux écrans** (haut/bas) + un panneau. Les apps multiples deviennent des onglets. |
| ![Sélecteur d'apps](docs/images/picker.png) | **+ App** : choisissez la zone, puis l'application. Toutes vos apps Linux sont là. |
| ![Applets](docs/images/applets.png) | **Des applets** dans le panneau : horloge, notes, calculatrice, musique, rappels. |

## Logiciel intégré : FM-Song Tracker

![FM-Song Tracker](docs/images/fmtracker.png)

Un **tracker** de musique : on compose en posant des notes dans une grille, jouées
par un synthé **MIDI** (fluidsynth + SoundFont General MIDI). Il rouvre même les
anciens morceaux **`.fms`** de FM-Song. Pilotable au clavier (saisie des notes) et à
la souris (lecture, instruments, patterns).

## Installation express

```sh
sudo apt install ./focusde_0.1.0_all.deb     # ou : sudo ./scripts/install.sh --login
```

Tout nouvel utilisateur (`adduser …`) obtient ensuite Focus DE automatiquement.
Détails → **[Guide d'installation](docs/install.md)**.

## En savoir plus

- 📖 **[Manuel d'utilisation](docs/user-manual.md)** — activités, zones, apps, applets,
  FM-Song Tracker, raccourcis.
- 🛠️ **[Guide d'installation](docs/install.md)**.
- 🧰 **[Détails techniques du shell](docs/desktop.md)** (pour contribuer).

---

> **Statut** : en développement. Le bureau et le tracker tournent sur Raspberry Pi 4
> (Sway/Wayland). Les retours sont les bienvenus.
