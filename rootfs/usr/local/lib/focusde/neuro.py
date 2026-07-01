#!/usr/bin/env python3
# Focus DE — Professeur Neuro : assistant de chat GTK, léger, qui parle DIRECTEMENT
# à Ollama (http://127.0.0.1:11434). Pas de Node, pas de navigateur, pas de config :
# l'endpoint et la persona sont en dur, ça marche tout seul. Look pastel Focus DE,
# avatar en haut, et mémoire PAR ACTIVITÉ (l'historique est stocké par slug de
# workspace, donc chaque activité garde son propre fil).
import gi, os, sys, json, threading, urllib.request
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
GLib.set_prgname("focus-assistant")

OLLAMA_URL = os.environ.get("NEURO_OLLAMA", "http://127.0.0.1:11434/api/chat")
MODEL = os.environ.get("NEURO_MODEL", "qwen2.5:1.5b")
ASSET = os.path.join(LIB, "assistant")
CONFDIR = os.path.expanduser("~/.config/focus/assistant")

def _card():
    try:
        return json.load(open(os.path.join(ASSET, "professeur-neuro.json"), encoding="utf-8")).get("data", {})
    except Exception:
        return {}
CARD = _card()
SYSTEM = CARD.get("system_prompt") or CARD.get("description") \
    or "Tu es le Professeur Neuro, un hibou savant bienveillant. Réponds en français, tutoie, reste bref."
GREETING = CARD.get("first_mes") or "Hou-hou ⚡ Te revoilà ! Sur quelle énigme on se penche ?"
AVATAR = os.path.join(ASSET, "neuro_avatar.png")

def scope():
    return focus_theme.focused_ws_name() or "Accueil"

def hist_path(sc):
    return os.path.join(CONFDIR, focus_theme.slug(sc) + ".json")

def load_hist(sc):
    try:
        return json.load(open(hist_path(sc), encoding="utf-8"))
    except Exception:
        return []

def save_hist(sc, msgs):
    os.makedirs(CONFDIR, exist_ok=True)
    json.dump(msgs, open(hist_path(sc), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

CSS = """
window { background: @bg@; }
.head { background: @surface@; border-bottom: 1px solid @border@; padding: 8px 12px; }
.name { font-size: 15px; font-weight: bold; color: @ink@; }
.sub  { font-size: 11px; color: @ink_soft@; }
.avatar { border-radius: 22px; }
.bubble-neuro { background: @surface@; border: 1px solid @border@; border-radius: 14px; padding: 8px 12px; margin: 2px 40px 2px 8px; }
.bubble-user  { background: @accent@; border-radius: 14px; padding: 8px 12px; margin: 2px 8px 2px 40px; }
.bubble-neuro label { color: @ink@; font-size: 14px; }
.bubble-user label  { color: @accent_ink@; font-size: 14px; }
.inputrow { background: @surface@; border-top: 1px solid @border@; padding: 8px; }
.inputrow entry { background: @bg@; color: @ink@; border-radius: 12px; padding: 8px 10px; border: 1px solid @border@; }
.send { background: @accent_strong@; color: @accent_ink@; border-radius: 12px; padding: 6px 16px; font-weight: bold; }
.send:hover { background: @accent@; }
"""

class Neuro(Gtk.Window):
    def __init__(self):
        super().__init__(title="Professeur Neuro")
        self.scope = scope()
        self.msgs = load_hist(self.scope)
        self.streaming = False
        self.cur_label = None
        self.cur_text = ""

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # --- en-tête : avatar + nom ---
        head = Gtk.Box(spacing=10); head.get_style_context().add_class("head")
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(AVATAR, 44, 44)
            av = Gtk.Image.new_from_pixbuf(pb); av.get_style_context().add_class("avatar")
            head.pack_start(av, False, False, 0)
        except Exception:
            pass
        tt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        nm = Gtk.Label(label="Professeur Neuro"); nm.set_xalign(0); nm.get_style_context().add_class("name")
        sb = Gtk.Label(label="assistant · %s" % self.scope); sb.set_xalign(0); sb.get_style_context().add_class("sub")
        tt.pack_start(nm, False, False, 0); tt.pack_start(sb, False, False, 0)
        head.pack_start(tt, False, False, 0)
        root.pack_start(head, False, False, 0)

        # --- fil de discussion ---
        self.scroll = Gtk.ScrolledWindow(); self.scroll.set_vexpand(True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for m in ("top", "bottom", "start", "end"): getattr(self.col, "set_margin_" + m)(6)
        self.scroll.add(self.col); root.pack_start(self.scroll, True, True, 0)

        # --- saisie ---
        row = Gtk.Box(spacing=6); row.get_style_context().add_class("inputrow")
        self.entry = Gtk.Entry(); self.entry.set_placeholder_text("Écris à Neuro…")
        self.entry.set_hexpand(True); self.entry.connect("activate", self.on_send)
        send = Gtk.Button(label="Envoyer"); send.get_style_context().add_class("send")
        send.connect("clicked", self.on_send)
        row.pack_start(self.entry, True, True, 0); row.pack_end(send, False, False, 0)
        root.pack_start(row, False, False, 0)

        # historique existant, sinon salutation
        if not self.msgs:
            self.bubble("assistant", GREETING)
            self.msgs.append({"role": "assistant", "content": GREETING})
            save_hist(self.scope, self.msgs)
        else:
            for m in self.msgs:
                self.bubble(m["role"], m["content"])

    def bubble(self, role, text):
        align = Gtk.Align.END if role == "user" else Gtk.Align.START
        box = Gtk.Box(); box.set_halign(align)
        box.get_style_context().add_class("bubble-user" if role == "user" else "bubble-neuro")
        lbl = Gtk.Label(label=text); lbl.set_line_wrap(True); lbl.set_xalign(0)
        lbl.set_selectable(True); lbl.set_max_width_chars(38)
        box.add(lbl)
        self.col.pack_start(box, False, False, 0)
        self.col.show_all()
        GLib.idle_add(self._to_bottom)
        return lbl

    def on_send(self, *_):
        if self.streaming:
            return
        text = self.entry.get_text().strip()
        if not text:
            return
        self.entry.set_text("")
        self.bubble("user", text)
        self.msgs.append({"role": "user", "content": text})
        save_hist(self.scope, self.msgs)
        self.cur_label = self.bubble("assistant", "…")
        self.cur_text = ""
        self.streaming = True
        threading.Thread(target=self._stream, daemon=True).start()

    def _stream(self):
        payload = {"model": MODEL, "stream": True,
                   "messages": [{"role": "system", "content": SYSTEM}]
                   + [{"role": m["role"], "content": m["content"]} for m in self.msgs]}
        try:
            req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                for raw in r:
                    raw = raw.strip()
                    if not raw:
                        continue
                    d = json.loads(raw)
                    tok = d.get("message", {}).get("content", "")
                    if tok:
                        GLib.idle_add(self._append, tok)
                    if d.get("done"):
                        break
        except Exception as e:                       # noqa: BLE001
            GLib.idle_add(self._append, "\n[Hou… souci de connexion à Ollama : %s]" % e)
        GLib.idle_add(self._finish)

    def _append(self, tok):
        self.cur_text += tok
        if self.cur_label:
            self.cur_label.set_text(self.cur_text)
        self._to_bottom()
        return False

    def _finish(self):
        self.streaming = False
        self.msgs.append({"role": "assistant", "content": self.cur_text})
        save_hist(self.scope, self.msgs)
        return False

    def _to_bottom(self):
        adj = self.scroll.get_vadjustment()
        if adj:
            adj.set_value(adj.get_upper())
        return False

def main():
    pal = focus_theme.for_activity(focus_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css(CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Neuro(); w.connect("destroy", Gtk.main_quit)
    w.set_default_size(420, 640)
    w.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
