#!/usr/bin/env python3
# Focus DE — récupération de SOURCES pour Professeur Neuro (RAG hybride) :
#   - Web fiable via Tavily : domaines de confiance (éducatif/académique), Wikipédia EXCLU
#     -> nécessite une clé gratuite (champ « tavily_key » du config assistant).
#   - Bases académiques via OpenAlex (sans clé), pour les questions pointues.
# gather() renvoie un bloc texte « SOURCES … » à injecter dans le system prompt.
# Tout est tolérant aux pannes : sans clé ou en cas d'échec réseau, on renvoie ce qu'on
# peut (voire une chaîne vide), et Neuro répond quand même.
import json, re, time, urllib.request, urllib.parse

TAVILY_URL = "https://api.tavily.com/search"
OPENALEX_URL = "https://api.openalex.org/works"
UA = "curl/8.5.0"                       # sinon certains fronts (Cloudflare) bloquent urllib
# OpenAlex : le mailto place dans le « polite pool » (moins de rate-limit).
OPENALEX_MAILTO = "focusde@localhost"
OPENALEX_UA = "FocusDE/1.0 (mailto:%s)" % OPENALEX_MAILTO

# Domaines de confiance (éducatif / académique). Wikipédia volontairement absent + exclu.
TRUSTED = [
    "education.gouv.fr", "eduscol.education.fr", "lumni.fr", "cnrs.fr", "cea.fr",
    "inserm.fr", "ird.fr", "ledevoir.com", "universalis.fr", "larousse.fr",
    "britannica.com", "futura-sciences.com", "nationalgeographic.fr", "pourlascience.fr",
    "nasa.gov", "esa.int", "noaa.gov", "nature.com", "sciencedirect.com",
    "edu", "ac.uk", "univ-lille.fr", "sorbonne-universite.fr", "universite-paris-saclay.fr",
]
EXCLUDE = ["wikipedia.org", "wikimedia.org", "m.wikipedia.org", "wikimini.org"]

# On ne lance une recherche que sur une vraie question (pas sur « merci », « ok »…).
_Q_HINT = re.compile(
    r"\?|pourquoi|comment|qu'?est|c'?est quoi|combien|explique|défini|définit|"
    r"qui (?:est|sont|était)|quand|où\b|quelle?s?\b|raconte|décri|à quoi|signifie",
    re.I)


def needs_search(q):
    q = (q or "").strip()
    return bool(q) and (len(q.split()) >= 4 or bool(_Q_HINT.search(q)))


def _post(url, payload, timeout=12):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url, timeout=8, ua=UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def web_sources(query, api_key, n=3):
    if not api_key:
        return []
    try:
        d = _post(TAVILY_URL, {
            "api_key": api_key, "query": query, "max_results": n,
            "search_depth": "basic", "include_answer": False,
            "include_domains": TRUSTED, "exclude_domains": EXCLUDE,
        })
        return [{"title": r.get("title", ""), "url": r.get("url", ""),
                 "text": (r.get("content") or "").strip()}
                for r in (d.get("results") or [])[:n]]
    except Exception:
        return []


def _openalex_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, places in inv.items():
        for p in places:
            pos[p] = word
    return " ".join(pos[k] for k in sorted(pos))


def academic_sources(query, n=2):
    q = urllib.parse.urlencode({"search": query, "per-page": n, "mailto": OPENALEX_MAILTO})
    url = OPENALEX_URL + "?" + q
    d = None
    for attempt in (1, 2):                            # OpenAlex 503 sous charge = souvent transitoire
        try:
            d = _get(url, timeout=8, ua=OPENALEX_UA)
            break
        except Exception:
            if attempt == 1:
                time.sleep(1.5)
    if d is None:
        return []
    out = []
    for w in (d.get("results") or [])[:n]:
        ab = _openalex_abstract(w.get("abstract_inverted_index"))
        if not ab:
            continue
        out.append({"title": w.get("title", ""),
                    "url": w.get("doi") or w.get("id") or "",
                    "text": ab})
    return out


def gather(query, tavily_key="", academic=True):
    """Renvoie un bloc « SOURCES … » (ou "" si rien). academic=False pour les plus jeunes."""
    if not needs_search(query):
        return ""
    srcs = web_sources(query, tavily_key)
    if academic:
        srcs += academic_sources(query)
    if not srcs:
        return ""
    lines = ["\n\nSOURCES FIABLES (appuie-toi dessus en priorité pour être exact ; "
             "n'utilise JAMAIS Wikipédia) :"]
    for i, s in enumerate(srcs, 1):
        txt = re.sub(r"\s+", " ", s.get("text", "")).strip()[:500]
        title = (s.get("title") or "").strip()
        lines.append("[%d] %s — %s\n%s" % (i, title, s.get("url", ""), txt))
    lines.append("Synthétise ces sources à la portée de l'élève, sans jargon inutile. "
                 "Si elles sont insuffisantes ou hors sujet, complète prudemment et "
                 "signale-le. Ne recopie pas les sources telles quelles.")
    return "\n".join(lines)


if __name__ == "__main__":            # test rapide : python3 neuro_search.py "pourquoi le ciel est bleu"
    import sys
    print(gather(" ".join(sys.argv[1:]) or "pourquoi le ciel est bleu", academic=True))
