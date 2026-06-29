#!/usr/bin/env python3
# Focus DE activity manager v2 : construction fiable, marques par-activite, accueil.
import subprocess, json, time, os, sys
DN = subprocess.DEVNULL
import os; HOME = os.path.expanduser("~")
LIBDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIBDIR)
import focus_applets

def sw(c): subprocess.run(["swaymsg", "-q", c], stdout=DN, stderr=DN)
def get(t):
    try: return json.loads(subprocess.check_output(["swaymsg", "-t", t]))
    except Exception: return None
def marks():
    m = get("get_marks"); return m if isinstance(m, list) else []
def focused_ws():
    for w in (get("get_workspaces") or []):
        if w.get("focused"): return w
    return None
def free_num():
    used = {w.get("num") for w in (get("get_workspaces") or [])}
    n = 1
    while n in used: n += 1
    return n

def launch_get(cmd):
    p = subprocess.Popen(["swaymsg","-t","subscribe","-m","-r",'["window"]'], stdout=subprocess.PIPE, text=True)
    time.sleep(0.3)
    subprocess.Popen(cmd, stdout=DN, stderr=DN, stdin=DN, start_new_session=True, env=dict(os.environ))
    dec = json.JSONDecoder(); buf = ""; t0 = time.time()
    while time.time()-t0 < 40:
        line = p.stdout.readline()
        if not line: continue
        buf += line
        while buf.strip():
            s = buf.lstrip()
            try: ev, i = dec.raw_decode(s)
            except ValueError: break
            buf = s[i:]
            if isinstance(ev, dict) and ev.get("change") == "new":
                cid = ev["container"]["id"]; p.terminate(); return cid
    p.terminate(); return None

def force_tabbed(cid):
    # cid a un frere -> split cree un vrai sous-conteneur, puis on le tabbe
    sw("[con_id=%d] focus" % cid); sw("split horizontal"); sw("layout tabbed")

def build_activity(ws, name, left=False):
    # Nouvelle activite = hub vide en zone principale (l'utilisateur le remplit via + > Raccourci).
    sw("workspace %s" % ws); time.sleep(0.3)
    sw('rename workspace to "%s"' % name)
    add("primary", ["python3", LIBDIR + "/hub.py", "--custom", name])
    add("left", ["python3", LIBDIR + "/panel_host.py"])   # panneau (avec le bouton "+")
    print("activite (hub vide) ws=%s name=%s" % (ws, name))

def ws_window_ids(wsid):
    tree = get("get_tree"); res = []
    if not tree: return res
    def find(n):
        if n.get("type") == "workspace" and n.get("id") == wsid: return n
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            r = find(c)
            if r: return r
        return None
    wsn = find(tree)
    if not wsn: return res
    def leaves(n):
        kids = (n.get("nodes") or []) + (n.get("floating_nodes") or [])
        if not kids and n.get("app_id") is not None:
            res.append(n["id"]); return
        for c in kids: leaves(c)
    leaves(wsn); return res

def recreate_zone(zone, wsid, cid):
    # La zone n'existe pas (activite vierge, ou zone videe). On forme le layout a la volee.
    pref = {"primary":"Zp", "secondary":"Zs", "left":"Zl"}[zone]
    sw("[con_id=%d] floating disable" % cid)   # jeux SDL (frozen-bubble=perl) s'ouvrent flottants
    others = [w for w in ws_window_ids(wsid) if w != cid]
    if not others:
        # 1re fenetre de l'activite : la zone occupe tout, en conteneur tabbed
        sw("[con_id=%d] focus" % cid); sw("layout tabbed")
        sw("[con_id=%d] mark %s_%d" % (cid, pref, wsid))
        return
    # du contenu existe : placer cid au bon endroit (orientation verticale par defaut) + onglets
    sw("[con_id=%d] focus" % cid)
    if zone == "left":
        # panneau gauche = colonne en PILE verticale (sortir du conteneur tabbed du workspace)
        sw("[con_id=%d] focus" % cid)
        sw("move left"); sw("move left")   # pop hors du tabbed -> splith[gauche, reste]
        sw("[con_id=%d] focus" % cid); sw("split vertical")
        sw("[con_id=%d] resize set width 260 px" % cid)
        sw("[con_id=%d] mark %s_%d" % (cid, pref, wsid))
        return
    if zone == "primary":
        sw("move up")
    elif zone == "secondary":
        sw("move down")
    force_tabbed(cid)
    sw("[con_id=%d] mark %s_%d" % (cid, pref, wsid))
    if zone == "secondary":
        sw("[con_id=%d] resize set height 33 ppt" % cid)   # split 2/3 - 1/3

def add(zone, cmd):
    ws = focused_ws()
    if not ws: print("no ws"); return 1
    pref = {"primary":"Zp", "secondary":"Zs", "left":"Zl"}.get(zone)
    if not pref: print("zone inconnue"); return 1
    wsid = ws["id"]; mark = "%s_%d" % (pref, wsid)
    cid = launch_get(cmd)
    if cid is None: print("pas de fenetre"); return 1
    if mark in marks():
        sw("[con_id=%d] floating disable" % cid)   # jeux SDL flottants -> tile dans la zone
        sw("[con_id=%d] move container to mark %s" % (cid, mark))
        print("ajoute -> %s" % mark)
    else:
        recreate_zone(zone, wsid, cid)
        print("zone recreee -> %s" % mark)
    sw("[con_id=%d] focus" % cid)
    return 0

def has_app(app_id):
    def scan(n):
        if n.get("app_id") == app_id: return True
        for c in (n.get("nodes") or []) + (n.get("floating_nodes") or []):
            if scan(c): return True
        return False
    t = get("get_tree"); return bool(t and scan(t))

def build_home():
    if has_app("focus-home"):          # already built -> idempotent, just go there
        sw("workspace Accueil"); return
    sw('[app_id="focus-panel"] kill'); time.sleep(0.3)   # clear any stray half-built panel
    names = [w.get("name") for w in (get("get_workspaces") or [])]
    if "Accueil" in names:
        sw("workspace Accueil")
    else:
        sw("rename workspace to Accueil")   # au boot : renommer la courante (le switch ne prend pas tot)
    time.sleep(0.4)
    # panneau gauche = UNE fenetre hote empilant les applets (defaut accueil : horloge + notes)
    L = launch_get(["python3", LIBDIR + "/panel_host.py"]); time.sleep(0.6)
    sw("[con_id=%d] focus" % L); sw("split horizontal")
    M = launch_get(["python3", LIBDIR + "/home.py"]); time.sleep(0.6)     # zone principale (app accueil)
    sw("[con_id=%d] focus" % L); sw("resize set width 240 px")
    # marquer le panneau (comme une activite) pour que "+ Applet" le remplace au lieu d'en creer un 2e
    ws = focused_ws()
    if ws: sw("[con_id=%d] mark Zl_%d" % (L, ws["id"]))
    print("home built L=%s M=%s" % (L, M))

def hub(category):
    # Ouvre (ou cree) une activite "hub" : Naviguer=firefox ; sinon l'app hub.py de la categorie.
    names = [w.get("name") for w in (get("get_workspaces") or [])]
    if category in names:
        sw("workspace " + category); return
    ws = str(free_num()); sw("workspace " + ws); time.sleep(0.3)
    sw('rename workspace to "%s"' % category)
    if category == "Naviguer":
        add("primary", ["env", "MOZ_ENABLE_WAYLAND=1", "firefox-esr",
                        "--profile", HOME + "/.mozilla/firefox/focus", "--new-window", "about:blank"])
    else:
        add("primary", ["python3", LIBDIR + "/hub.py", category])
    print("hub %s sur ws %s" % (category, ws))

def rebuild_panel():
    # (re)construit le panneau gauche (UNE fenetre panel_host) selon la selection d'applets.
    ws = focused_ws()
    if not ws: print("no ws"); return
    wsid = ws["id"]; mark = "Zl_%d" % wsid
    if mark in marks():
        # tuer UNIQUEMENT la fenetre du panneau (pas focus parent : sur une fenetre unique
        # ca selectionnerait le conteneur de l'espace -> tuerait aussi la section principale)
        sw("[con_mark=%s] kill" % mark); time.sleep(0.8)
    # le panneau est toujours present (il porte le bouton "+"), meme sans applet
    add("left", ["python3", LIBDIR + "/panel_host.py"])
    print("panel reconstruit (%d applets)" % len(focus_applets.load_applet_sel(ws.get("name"))))

def open_agenda():
    # Ouvre (ou bascule vers) l'activite "Agenda" avec l'app agenda.py en zone principale.
    names = [w.get("name") for w in (get("get_workspaces") or [])]
    if "Agenda" in names:
        sw("workspace Agenda")
    else:
        ws = str(free_num()); sw("workspace " + ws); time.sleep(0.3)
        sw('rename workspace to "Agenda"')
        add("primary", ["python3", LIBDIR + "/agenda.py"])
    print("agenda")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print("usage: new [--auto|<ws>] <name> [--left] | add <zone> <cmd...> | home | agenda"); sys.exit(2)
    if a[0] == "new":
        left = "--left" in a
        rest = [x for x in a[1:] if x != "--left"]
        if rest and rest[0] == "--auto":
            name = " ".join(rest[1:]) or "Activité"; ws = str(free_num())
        else:
            ws = rest[0]; name = " ".join(rest[1:]) or ("Activité " + ws)
        build_activity(ws, name, left=left)
    elif a[0] == "add":
        sys.exit(add(a[1], a[2:]))
    elif a[0] == "home":
        build_home()
    elif a[0] == "hub":
        hub(" ".join(a[1:]))
    elif a[0] == "agenda":
        open_agenda()
    elif a[0] == "panel":
        rebuild_panel()
