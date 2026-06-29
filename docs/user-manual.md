# Focus DE — Manuel d'utilisation

Focus DE est un environnement de bureau Linux **organisé par activités** plutôt que
par fenêtres en vrac. Il est pensé pour rester simple et lisible (look pastel, sans
bordures), aussi bien pour une démonstration que pour un Raspberry Pi familial.

---

## 1. Le concept

Au lieu d'empiler des fenêtres sur un bureau, Focus DE regroupe ce que vous faites
en **activités**. Une activité, c'est un contexte (un projet, un jeu, une session de
travail…) qui occupe tout l'écran et se découpe en **zones**. Quand vous prenez du
recul, vous retombez sur l'**Accueil** : la vue d'ensemble de vos activités.

C'est inspiré du bureau *Sugar* (OLPC) : on « zoome » entre la vue d'ensemble
(l'Accueil) et une activité précise.

Trois idées suffisent pour tout comprendre :

- **Activité** — un espace plein écran dédié à une tâche (= un *workspace* Sway).
- **Zone** — une activité se divise en *écran principal* (haut), *écran secondaire*
  (bas) et un *panneau* à gauche.
- **Applet** — une petite vignette utilitaire (horloge, notes…) posée dans le panneau.

---

## 2. Le bureau en un coup d'œil

![L'Accueil de Focus DE](images/home.png)

En haut, une **barre** discrète :

| Élément | Rôle |
|--------|------|
| *(à gauche)* nom de l'activité | l'activité courante |
| **+ App** | ajouter une application (ouvre le sélecteur) |
| **Panneau** | afficher / masquer le panneau d'applets |
| **Accueil** | revenir à la vue d'ensemble |
| *(à droite)* horloge | l'heure |

---

## 3. L'Accueil

L'Accueil est votre point de départ (cliquez **Accueil** dans la barre à tout moment).
On y trouve :

- un **bonjour** personnalisé et la date ;
- des **cartes** d'état (*Reprendre*, *En ce moment*, *Aujourd'hui*) ;
- les **tuiles de hubs** (*Travailler, Apprendre, Jouer, Naviguer, Créer*) — voir §7 ;
- vos **activités** ouvertes (une tuile colorée chacune) ;
- la tuile **+ Nouvelle activité** ;
- à gauche, le **panneau d'applets** (par défaut : Horloge + Notes).

---

## 4. Les activités

**Créer une activité** : cliquez la tuile **+ Nouvelle activité**, donnez-lui un nom.
Elle s'ouvre vide, prête à être remplie d'applications.

**Basculer entre activités** : cliquez sa tuile depuis l'Accueil. (Sous le capot,
chaque activité est un espace de travail Sway ; `Super`+`1`…`9` fonctionne aussi.)

---

## 5. Les zones : écran principal, secondaire et panneau

![Une activité avec deux zones (haut/bas) et le panneau](images/activity-zones.png)

Une activité se compose de trois zones :

- **Écran principal** (en haut) — la zone de travail principale ;
- **Écran secondaire** (en bas) — une seconde zone, par ex. un terminal ou des notes ;
- **Panneau** (à gauche) — accueille les applets et le bouton **+**.

Quand une zone contient plusieurs applications, elles se rangent en **onglets**
(barres colorées en haut de la zone). 

**Agrandir une zone** (plein écran temporaire) :

- `Super`+`Page ↑` → agrandir l'**écran principal** ;
- `Super`+`Page ↓` → agrandir l'**écran secondaire**.

---

## 6. Ajouter une application

![Le sélecteur d'applications (+ App)](images/picker.png)

Cliquez **+ App** dans la barre (ou `Super`+`T`). Le sélecteur s'ouvre :

1. Choisissez **où** l'ajouter : **En haut** (écran principal), **En bas** (écran
   secondaire), ou **Raccourci (hub)** pour l'épingler dans un hub (§7).
2. Cherchez/cliquez l'application — la liste reprend **toutes** les applications
   installées sur le système.

L'application s'ouvre dans la zone choisie (en onglet si la zone est déjà occupée).

---

## 7. Les hubs (catégories d'applications)

![Le hub « Créer »](images/hub-creer.png)

Depuis l'Accueil, les tuiles **Travailler / Apprendre / Jouer / Naviguer / Créer**
ouvrent un **hub** : une grille d'applications de cette catégorie, remplie
automatiquement d'après les catégories standard *freedesktop* :

| Hub | Contenu |
|-----|---------|
| **Travailler** | bureautique (traitement de texte, tableur, finance…) |
| **Apprendre** | logiciels éducatifs |
| **Jouer** | jeux |
| **Naviguer** | le navigateur web |
| **Créer** | outils de **création** — graphisme **et** audio/musique |

> Le hub **Créer** distingue la *création* de la *consultation* : il affiche les
> éditeurs (dessin, retouche, tracker audio…) et **exclut** les simples visualiseurs
> d'images/documents et lecteurs multimédia.

Vous pouvez aussi **épingler** n'importe quelle application dans un hub via le
sélecteur (**+ App** → zone **Raccourci (hub)**).

---

## 8. Les applets (panneau de gauche)

![Le gestionnaire d'applets](images/applets.png)

Le panneau de gauche héberge des **applets**. Cliquez le **+** en haut du panneau
(« Applets ») pour choisir ceux à afficher, puis **Appliquer**.

| Applet | Description | Utilisation |
|--------|-------------|-------------|
| **Horloge** | Heure et date | affichage simple |
| **Notes** | Notes de l'activité (ou *partout* depuis l'Accueil) | **+ Nouvelle** pour ajouter ; l'**œil** affiche une note, la **corbeille** la supprime |
| **Calculatrice** | Petits calculs | calculs rapides sans quitter l'activité |
| **Musique** | Lecteur des fichiers de `~/Music` | écouter sa musique |
| **Rappel** | Prochains rendez-vous de l'agenda | aperçu de l'agenda |

Le bouton **Panneau** de la barre affiche/masque le panneau.

---

## 9. Logiciels intégrés

### FM-Song Tracker

![FM-Song Tracker avec un morceau chargé](images/fmtracker.png)

**FM-Song Tracker** est un *tracker* de musique : on compose en plaçant des notes
dans une grille. Le son est produit par un synthétiseur **MIDI** (fluidsynth) avec
une banque d'instruments *General MIDI* — des centaines d'instruments disponibles.
Il importe aussi les anciens morceaux **`.fms`** du logiciel FM-Song d'origine.

**Lancer** : depuis le hub **Créer**, via **+ App**, ou en ligne de commande
`fmtracker mon_morceau.fms`. Le bouton **Open .fms** ouvre un morceau existant.

**Lire la grille** : chaque **colonne** est un canal (un instrument), chaque **ligne**
est un pas (le temps qui avance vers le bas).

- `----` : case vide (la note précédente continue) ;
- `===` : silence (arrêt de la note) ;
- `C-5`, `F#4`… : une note jouée.

**Saisie au clavier** :

| Touche | Action |
|--------|--------|
| `C D E F G A B` | saisir la note correspondante |
| `+` / `-` | monter / descendre d'une **octave** |
| `Ctrl`+`+` / `Ctrl`+`-` (ou `Ctrl`+`↑`/`↓`) | transposer la case d'un **demi-ton** |
| `↑ ↓` | déplacer le curseur dans le temps |
| `← →` | changer de **canal** |
| `Espace` | insérer un **silence** |
| `Suppr` | effacer la case |

**Souris (barre d'outils)** : **▶ Play**, **❚❚ Pause**, **Resume**, **■ Stop** ;
**+ Channel** / **+ Pattern** ; réglage du **BPM** ; choix du **Pattern** ; choix de
l'**Instrument** (preset General MIDI) du canal courant.

Pendant la lecture, la grille **défile** pour suivre la tête de lecture, et
**enchaîne les patterns** selon la liste de lecture, en boucle.

---

## 10. Raccourcis clavier

`Super` = la touche logo (Windows / ⌘).

| Raccourci | Action |
|-----------|--------|
| `Super`+`T` | **+ App** (sélecteur d'applications) |
| `Super`+`Maj`+`T` | changer le **thème** |
| `Super`+`Page ↑` / `Page ↓` | agrandir l'écran **principal** / **secondaire** |
| `Super`+`Entrée` | ouvrir un **terminal** |
| `Super`+`D` | menu d'applications (fuzzel) |
| `Super`+`flèches` | changer la fenêtre active |
| `Super`+`Maj`+`flèches` | déplacer la fenêtre |
| `Super`+`1`…`9` | aller à une activité |
| `Super`+`Maj`+`Q` | fermer la fenêtre |
| `Super`+`Maj`+`C` | recharger Focus DE (Sway) |

---

Voir aussi : [installation](install.md) · [présentation du projet](../README.md).
