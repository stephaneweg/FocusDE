#!/usr/bin/env python3
# Onyx / Focus DE - registre des VRAIS applets du panneau gauche.
# Le gestionnaire d'applets (applet_mgr.py) ne propose que ceux-ci.
import os, json, re
import os; HOME = os.path.expanduser("~")
CONF = os.path.expanduser("~/.config/onyx")

# Chaque applet est un module exposant make(ctx)->Gtk.Box, CSS (str), EXPAND (bool).
# expand=True : l'applet prend la hauteur restante (listes) ; False : hauteur naturelle.
APPLETS = [
    {"id": "clock", "name": "Horloge", "icon": "clock", "module": "applet_clock",
     "desc": "Heure et date", "expand": False},
    {"id": "notes", "name": "Notes", "icon": "accessories-text-editor", "module": "applet_notes",
     "desc": "Notes de l'activité (ou partout depuis l'accueil)", "expand": True},
    {"id": "calc", "name": "Calculatrice", "icon": "accessories-calculator", "module": "applet_calc",
     "desc": "Petits calculs", "expand": False},
    {"id": "music", "name": "Musique", "icon": "multimedia-audio-player", "module": "applet_music",
     "desc": "Lecteur des fichiers de ~/Music", "expand": True},
    {"id": "fmplayer", "name": "FM-Player", "icon": "audio-x-generic", "module": "applet_fmplayer",
     "desc": "Joue des morceaux FM-Song (.fms) : un fichier ou un dossier", "expand": True},
    {"id": "rappel", "name": "Rappel", "icon": "x-office-calendar", "module": "applet_rappel",
     "desc": "Prochains rendez-vous de l'agenda", "expand": True},
]
DEFAULT_HOME = ["clock", "notes"]   # applets de l'accueil par defaut

def by_id(aid):
    for a in APPLETS:
        if a["id"] == aid:
            return a
    return None

def applet_sel_path(ws):
    return os.path.join(CONF, "applets", slug(ws))

def load_applet_sel(ws):
    # liste d'ids d'applets pour cette activite ; defaut = DEFAULT_HOME sur l'accueil, sinon vide.
    try:
        ids = [l.strip() for l in open(applet_sel_path(ws), encoding="utf-8") if l.strip()]
    except Exception:
        return list(DEFAULT_HOME) if (ws or "") == "Accueil" else []
    return [i for i in ids if by_id(i)]

def save_applet_sel(ws, ids):
    p = applet_sel_path(ws); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(ids))

# --- stockage des NOTES (contextuelles a l'activite ; "__global__" = partout/accueil) ---
def slug(n): return re.sub(r'[^a-zA-Z0-9]+', '_', n or "").strip('_') or "act"

def notes_scope(ws_name):
    if not ws_name or ws_name == "Accueil":
        return "__global__"
    return slug(ws_name)

def scope_label(scope):
    return "Partout" if scope == "__global__" else "Cette activité"

def notes_path(scope):
    return os.path.join(CONF, "notes", scope + ".json")

def load_notes(scope):
    try:
        return json.load(open(notes_path(scope), encoding="utf-8"))
    except Exception:
        return []

def save_notes(scope, notes):
    p = notes_path(scope); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(notes, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def upsert_note(scope, nid, title, body):
    notes = load_notes(scope)
    if nid is None:
        nid = max([n["id"] for n in notes] + [0]) + 1
        notes.append({"id": nid, "title": title, "body": body})
    else:
        for n in notes:
            if n["id"] == nid:
                n["title"] = title; n["body"] = body; break
    save_notes(scope, notes); return nid

def delete_note(scope, nid):
    save_notes(scope, [n for n in load_notes(scope) if n["id"] != nid])

def get_note(scope, nid):
    for n in load_notes(scope):
        if n["id"] == nid:
            return n
    return None

# --- stockage de l'AGENDA (partage par l'app agenda.py et l'applet Rappel) ---
AGENDA_PATH = os.path.join(CONF, "agenda.json")

def load_events():
    try:
        return json.load(open(AGENDA_PATH, encoding="utf-8"))
    except Exception:
        return []

def save_events(events):
    os.makedirs(os.path.dirname(AGENDA_PATH), exist_ok=True)
    events.sort(key=lambda e: (e.get("date", ""), e.get("time", "")))
    json.dump(events, open(AGENDA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def upsert_event(eid, date, tm, title, note):
    ev = load_events()
    if eid is None:
        eid = max([e["id"] for e in ev] + [0]) + 1
        ev.append({"id": eid, "date": date, "time": tm, "title": title, "note": note})
    else:
        for e in ev:
            if e["id"] == eid:
                e.update(date=date, time=tm, title=title, note=note); break
    save_events(ev); return eid

def delete_event(eid):
    save_events([e for e in load_events() if e["id"] != eid])

def get_event(eid):
    for e in load_events():
        if e["id"] == eid:
            return e
    return None

_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
         "septembre", "octobre", "novembre", "décembre"]

def fr_date(iso):
    import datetime
    try:
        d = datetime.date.fromisoformat(iso)
    except Exception:
        return iso
    s = "%s %d %s" % (_JOURS[d.weekday()], d.day, _MOIS[d.month - 1])
    return s[0].upper() + s[1:]

def upcoming_events(limit=None):
    import datetime
    today = datetime.date.today().isoformat()
    ev = [e for e in load_events() if e.get("date", "") >= today]
    ev.sort(key=lambda e: (e.get("date", ""), e.get("time", "")))
    return ev[:limit] if limit else ev
