#!/usr/bin/env python3
# Focus DE — Professeur Neuro : assistant de chat GTK, léger, qui parle DIRECTEMENT
# à Ollama (http://127.0.0.1:11434). Pas de Node, pas de navigateur, pas de config :
# l'endpoint et la persona sont en dur, ça marche tout seul. Look pastel Focus DE,
# avatar en haut, et mémoire PAR ACTIVITÉ (l'historique est stocké par slug de
# workspace, donc chaque activité garde son propre fil).
import gi, os, sys, json, threading, urllib.request, re, subprocess, glob
LIB = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, LIB)
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
GLib.set_prgname("focus-assistant")

ASSET = os.path.join(LIB, "assistant")
CONFDIR = os.path.expanduser("~/.config/focus/assistant")

def _load_config():
    try:
        return json.load(open(os.path.join(CONFDIR, "config.json"), encoding="utf-8"))
    except Exception:
        return {}
_CFG = _load_config()
# API compatible OpenAI. Défaut = Groq ; on peut pointer Mistral/Gemini/un Ollama local
# via ~/.config/focus/assistant/config.json (base_url, model, api_key).
BASE_URL = os.environ.get("NEURO_BASE_URL") or _CFG.get("base_url") \
    or "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("NEURO_MODEL") or _CFG.get("model") or "llama-3.3-70b-versatile"
API_KEY = os.environ.get("NEURO_API_KEY") or _CFG.get("api_key") or ""

# --- Synthèse vocale (Piper, hors-ligne) ---
PIPER_BIN = os.path.expanduser("~/piper/piper/piper")
_voices = sorted(glob.glob(os.path.expanduser("~/piper/voices/*.onnx")))
PIPER_VOICE = _voices[0] if _voices else None
TTS_AVAILABLE = bool(PIPER_VOICE) and os.path.exists(PIPER_BIN)
TTS_WAV = "/tmp/neuro_tts_%d.wav" % os.getpid()

def save_config():
    try:
        p = os.path.join(CONFDIR, "config.json")
        json.dump(_CFG, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        os.chmod(p, 0o600)
    except Exception:
        pass

def _card():
    try:
        return json.load(open(os.path.join(ASSET, "professeur-neuro.json"), encoding="utf-8")).get("data", {})
    except Exception:
        return {}
CARD = _card()
SYSTEM = CARD.get("system_prompt") or CARD.get("description") \
    or "Tu es le Professeur Neuro, un hibou savant bienveillant. Réponds en français, tutoie, reste bref."
GREETING = CARD.get("first_mes") or "Te revoilà ⚡ Sur quelle énigme on se penche ?"
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
.tts { background: @bg@; border-radius: 12px; padding: 6px 10px; border: 1px solid @border@; }
.tts:hover { background: @accent@; }
"""

class Neuro(Gtk.Window):
    def __init__(self):
        super().__init__(title="Professeur Neuro")
        self.scope = scope()
        self.msgs = load_hist(self.scope)
        self.streaming = False
        self.cur_label = None
        self.cur_text = ""
        self.tts_on = TTS_AVAILABLE and bool(_CFG.get("tts", True))
        self._tts_stop = threading.Event()
        self._tts_cur = None
        self._tts_thread = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # --- en-tête : GRAND avatar d'humeur (pleine largeur) + nom ---
        head = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        head.get_style_context().add_class("head")
        self.avatar_img = Gtk.Image(); self.avatar_img.set_halign(Gtk.Align.CENTER)
        head.pack_start(self.avatar_img, False, False, 0)
        nm = Gtk.Label(label="Professeur Neuro"); nm.set_halign(Gtk.Align.CENTER)
        nm.get_style_context().add_class("name")
        sb = Gtk.Label(label="assistant · %s" % self.scope); sb.set_halign(Gtk.Align.CENTER)
        sb.get_style_context().add_class("sub")
        head.pack_start(nm, False, False, 0); head.pack_start(sb, False, False, 0)
        root.pack_start(head, False, False, 0)
        self.mood = None
        self.set_mood("content")                     # accueil = sourire

        # --- fil de discussion ---
        self.scroll = Gtk.ScrolledWindow(); self.scroll.set_vexpand(True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for m in ("top", "bottom", "start", "end"): getattr(self.col, "set_margin_" + m)(6)
        self.scroll.add(self.col); root.pack_start(self.scroll, True, True, 0)

        # --- saisie ---
        row = Gtk.Box(spacing=6); row.get_style_context().add_class("inputrow")
        if TTS_AVAILABLE:
            self.tts_btn = Gtk.Button(label="🔊" if self.tts_on else "🔇")
            self.tts_btn.get_style_context().add_class("tts")
            self.tts_btn.connect("clicked", self._toggle_tts)
            row.pack_start(self.tts_btn, False, False, 0)
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
        self._stop_speaking()                        # couper la voix en cours
        self.entry.set_text("")
        self.bubble("user", text)
        self.msgs.append({"role": "user", "content": text})
        save_hist(self.scope, self.msgs)
        self.cur_label = self.bubble("assistant", "…")
        self.cur_text = ""
        self.mood_parsed = False
        self.set_mood("pensif")                      # il réfléchit pendant la génération
        self.streaming = True
        threading.Thread(target=self._stream, daemon=True).start()

    MOODS = ("neutre", "content", "pensif", "surpris", "triste", "fier")

    def set_mood(self, mood):
        if mood == self.mood:
            return
        path = os.path.join(ASSET, "moods", mood + ".png")
        if not os.path.exists(path):
            path = AVATAR
        try:
            self.avatar_img.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(path, 132, 132))
            self.mood = mood
        except Exception:
            pass

    def _toggle_tts(self, btn):
        self.tts_on = not self.tts_on
        btn.set_label("🔊" if self.tts_on else "🔇")
        _CFG["tts"] = self.tts_on
        save_config()
        if not self.tts_on:
            self._stop_speaking()

    def _stop_speaking(self):
        self._tts_stop.set()
        p = self._tts_cur
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass

    def _start_speaking(self, text):
        self._stop_speaking()
        if self._tts_thread and self._tts_thread.is_alive():
            self._tts_thread.join(timeout=0.4)
        self._tts_stop = threading.Event()
        label = self.cur_label                          # bulle cible figée pour ce tour
        self._tts_thread = threading.Thread(target=self._speak, args=(text, label), daemon=True)
        self._tts_thread.start()

    def _speak(self, text, label):
        # Découpe en phrases. Pour chacune : on la SYNTHÉTISE (Piper), on l'AFFICHE dans
        # la bulle pile au moment où le son démarre (texte ↔ voix synchronisés), on la joue.
        parts = [p.strip() for p in re.split(r"(?<=[.!?…:])\s+", text.strip()) if p.strip()]
        shown = ""
        for sent in parts:
            if self._tts_stop.is_set():
                GLib.idle_add(self._set_reply, text, label)   # annulé -> tout afficher
                return
            tts = re.sub(r"\s+", " ", re.sub(r"[*#`>_\[\]]", " ", sent)).strip()
            try:
                if tts:
                    piper = subprocess.Popen([PIPER_BIN, "--model", PIPER_VOICE, "--output_file", TTS_WAV],
                                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._tts_cur = piper
                    piper.communicate(tts.encode("utf-8"))    # (bloque le temps de la synthèse)
            except Exception:
                GLib.idle_add(self._set_reply, text, label)
                return
            if self._tts_stop.is_set():
                GLib.idle_add(self._set_reply, text, label)
                return
            shown = (shown + " " + sent).strip()
            GLib.idle_add(self._set_reply, shown, label)      # afficher la phrase = début du son
            if tts:
                try:
                    play = subprocess.Popen(["aplay", "-q", TTS_WAV],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._tts_cur = play
                    play.wait()
                except Exception:
                    pass
        GLib.idle_add(self._set_reply, text, label)           # tout est affiché à la fin

    def _stream(self):
        if not API_KEY:
            GLib.idle_add(self._append, "Pas de clé API configurée. Ajoute ta clé dans "
                          "~/.config/focus/assistant/config.json (champ « api_key »).")
            GLib.idle_add(self._finish)
            return
        payload = {"model": MODEL, "stream": True,
                   "messages": [{"role": "system", "content": SYSTEM}]
                   + [{"role": m["role"], "content": m["content"]} for m in self.msgs]}
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY,
                   "User-Agent": "curl/8.5.0"}   # sinon Cloudflare bloque urllib (erreur 1010)
        try:
            req = urllib.request.Request(BASE_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                for raw in r:                        # flux SSE compatible OpenAI
                    raw = raw.strip()
                    if not raw or not raw.startswith(b"data:"):
                        continue
                    data = raw[5:].strip()
                    if data == b"[DONE]":
                        break
                    try:
                        d = json.loads(data)
                    except Exception:
                        continue
                    tok = ((d.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
                    if tok:
                        GLib.idle_add(self._append, tok)
        except Exception as e:                       # noqa: BLE001
            GLib.idle_add(self._append, "\n[souci de connexion : %s]" % e)
        GLib.idle_add(self._finish)

    def _append(self, tok):
        self.cur_text += tok
        if not self.mood_parsed:
            s = self.cur_text.lstrip()
            m = re.match(r"\[\s*(?:humeur\s*:\s*)?([a-zA-Zàâéèêïôùûç]+)\s*\]", s, re.I)
            if m and m.group(1).lower() in self.MOODS:  # tag humeur -> régler l'avatar + le retirer
                self.set_mood(m.group(1).lower())
                self.cur_text = s[m.end():].lstrip()
                self.mood_parsed = True
            elif (s and s[0] != "[") or len(s) > 24:  # pas de tag au début -> on affiche tel quel
                self.mood_parsed = True
            else:
                return False                         # tag encore en cours de réception : on attend
        # Avec la voix : on n'affiche PAS pendant le streaming — le texte apparaîtra
        # phrase par phrase, synchronisé avec l'audio (voir _speak). Sans voix : live.
        if not self.tts_on:
            self._set_reply(self.cur_text)
        return False

    def _set_reply(self, text, label=None):
        tgt = label if label is not None else self.cur_label
        if tgt is not None and tgt is self.cur_label:     # n'écris que dans la bulle courante
            tgt.set_text(text or "…")
            self._to_bottom()
        return False

    def _finish(self):
        self.streaming = False
        if not self.mood_parsed:
            self.set_mood("neutre")
        self.msgs.append({"role": "assistant", "content": self.cur_text})
        save_hist(self.scope, self.msgs)
        if self.tts_on and self.cur_text.strip():
            self._start_speaking(self.cur_text)     # lecture auto de la réponse
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
