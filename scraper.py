#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper.py — Moteur de surveillance (tourne automatiquement dans le cloud).

À chaque exécution :
  1. ouvre les 4 calendriers LNH dans un navigateur automatisé (Playwright) ;
  2. lit tous les matchs (équipes, journée, date, horaire) ;
  3. compare avec l'état précédent (data/state.json) ;
  4. régénère la page web docs/index.html (changements EN ROUGE) ;
  5. envoie un e-mail SI un horaire a changé.

Réglages via variables d'environnement (secrets GitHub) :
  SMTP_USER, SMTP_PASS, SMTP_HOST (def. smtp.gmail.com), SMTP_PORT (def. 587),
  MAIL_TO (destinataires séparés par des virgules), SITE_URL (lien de la page).
"""

import json
import os
import re
import sys
from datetime import datetime

import lnh_core as core

ICI = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ICI, "data", "state.json")
HISTO = os.path.join(ICI, "data", "historique.txt")
SITE = os.path.join(ICI, "docs", "index.html")

COMPETITIONS = [
    {"nom": "Daikin StarLigue",     "url": "https://www.lnh.fr/daikin-starligue/calendrier"},
    {"nom": "ProLigue",             "url": "https://www.lnh.fr/proligue/calendrier"},
    {"nom": "Coupe de France",      "url": "https://www.lnh.fr/autres-competitions/coupe-de-france"},
    {"nom": "Ligue des Champions",  "url": "https://www.lnh.fr/autres-competitions/ligue-des-champions"},
    {"nom": "Ligue Européenne EHF", "url": "https://www.lnh.fr/autres-competitions/coupe-ehf"},
]

# --------------------------------------------------------------------------
# Extraction dans le navigateur
# --------------------------------------------------------------------------

JS_EXTRACTION = r"""
() => {
  const out = []; const vus = new Set();
  for (const a of document.querySelectorAll('a[href*="/calendriers/"]')) {
    const href = a.getAttribute('href') || '';
    const m = href.match(/\/calendriers\/([^\/]+)\/([^\/]+)\/([^\/]+)\/([^\/]+)\/([^\/?#]+)/);
    if (!m || href.includes('/equipes/')) continue;
    const id = (m[2]+'/'+m[3]+'/'+m[4]+'/'+m[5]).toLowerCase();
    if (vus.has(id)) continue; vus.add(id);
    let el = a, texte = '';
    for (let i=0;i<6 && el;i++){ el = el.parentElement; if(!el) break;
      const t = el.innerText || '';
      if (/\b\d{1,2}\s+(janv|févr|fevr|mars|avr|mai|juin|juil|août|aout|sept|oct|nov|déc|dec)/i.test(t)){texte=t;break;}
      texte = t;
    }
    out.push({id, saison:m[1], tour:m[3], dom:m[4], ext:m[5], texte});
  }
  return out;
}
"""

_RE_HORAIRE = re.compile(
    r"(?P<wd>lun|mar|mer|jeu|ven|sam|dim)\.?\s+(?P<d>\d{1,2})\s+"
    r"(?P<mon>janvier|janv|février|fevrier|févr|fevr|mars|avril|avr|mai|juin|"
    r"juillet|juil|août|aout|septembre|sept|octobre|oct|novembre|nov|décembre|déc|dec)\.?"
    r"(?:\s*(?P<h>\d{1,2})\s*h\s*(?P<mi>\d{2})?)?", re.IGNORECASE)

_MOIS_COURT = {"janvier":"janv","janv":"janv","février":"févr","fevrier":"févr","févr":"févr",
    "fevr":"févr","mars":"mars","avril":"avr","avr":"avr","mai":"mai","juin":"juin",
    "juillet":"juil","juil":"juil","août":"août","aout":"août","septembre":"sept","sept":"sept",
    "octobre":"oct","oct":"oct","novembre":"nov","nov":"nov","décembre":"déc","déc":"déc","dec":"déc"}

_MOTS_PARASITES = re.compile(
    r"^(vs|infos?|stats?|billetterie|starmatch|suspense|daikin|proligue|ligue|coupe|troph|j\d+|\d+\s*-\s*\d+|\d{1,2}\s*h)",
    re.IGNORECASE)


def _slug_vers_nom(slug):
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())


def _horaire(texte):
    m = _RE_HORAIRE.search(texte or "")
    if not m:
        return ""
    wd = m.group("wd").lower(); d = int(m.group("d"))
    mon = _MOIS_COURT.get(m.group("mon").lower(), m.group("mon").lower())
    if m.group("h"):
        h = int(m.group("h")); mi = int(m.group("mi")) if m.group("mi") else 0
        return f"{wd}. {d} {mon}. {h}h{mi:02d}"
    return f"{wd}. {d} {mon}."


def _est_equipe(l):
    l = l.strip()
    if not (2 <= len(l) <= 32) or _MOTS_PARASITES.match(l):
        return False
    if re.search(r"\d", l) and not re.search(r"[A-Za-zÀ-ÿ]{3}", l):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]{2,}", l))


def _nom_match(texte, dom, ext):
    if texte:
        lignes = [x.strip() for x in texte.splitlines() if x.strip()]
        for i, l in enumerate(lignes):
            if l.lower() == "vs" and 0 < i < len(lignes) - 1:
                a, b = lignes[i-1], lignes[i+1]
                if _est_equipe(a) and _est_equipe(b):
                    return f"{a} – {b}"
    def net(s):
        n = _slug_vers_nom(s)
        return re.sub(r"\s+(Handball|Hb|Hbc)$", "", n).strip() or _slug_vers_nom(s)
    return f"{net(dom)} – {net(ext)}"


def _journee(tour):
    if re.fullmatch(r"j\d+", tour, re.IGNORECASE):
        return tour.upper()
    lib = tour.replace("-", " ").replace("eme", "e")
    lib = re.sub(r"journee", "Journée", lib, flags=re.IGNORECASE)
    return lib[:1].upper() + lib[1:]


def normaliser(bruts):
    return [{"id": b["id"], "journee": _journee(b.get("tour", "")),
             "match": _nom_match(b.get("texte", ""), b.get("dom", ""), b.get("ext", "")),
             "horaire": _horaire(b.get("texte", ""))} for b in bruts]


def _fermer_cookies(page):
    for txt in ["Continuer sans accepter", "Tout refuser", "Refuser", "Je refuse"]:
        try:
            b = page.get_by_text(re.compile(txt, re.I)).first
            if b and b.is_visible(timeout=700):
                b.click(timeout=1200); return
        except Exception:
            pass
    for sel in ['#didomi-notice-disagree-button', '[aria-label="Fermer"]', ".close"]:
        try:
            page.locator(sel).first.click(timeout=700); return
        except Exception:
            pass


_MOIS_NOMS = ["août", "aout", "septembre", "octobre", "novembre", "décembre",
              "decembre", "janvier", "février", "fevrier", "mars", "avril",
              "mai", "juin", "juillet"]


def _attendre_matchs(page, secondes=30):
    for _ in range(secondes):
        try:
            if page.locator('a[href*="/calendriers/"]').count() > 0:
                return True
        except Exception:
            pass
        page.wait_for_timeout(1000)
    return False


def _extraire(page):
    try:
        return normaliser(page.evaluate(JS_EXTRACTION))
    except Exception:
        return []


def _labels_options(sel):
    labels = []
    try:
        opts = sel.locator("option")
        for j in range(opts.count()):
            try:
                labels.append(opts.nth(j).inner_text().strip())
            except Exception:
                labels.append("")
    except Exception:
        pass
    return labels


def _choisir(page, sel, index):
    try:
        sel.select_option(index=index, timeout=1500)
        page.wait_for_timeout(1600)     # laisser le site recharger la liste
        return True
    except Exception:
        return False


def recuperer(page, comp):
    """Ouvre la compétition et parcourt TOUTES LES JOURNÉES et TOUS LES MOIS
    (chaque filtre balayé pendant que l'autre est sur « tout ») pour récupérer
    l'intégralité de la saison. Les matchs sont dédoublonnés par leur identifiant."""
    print(f"  → {comp['nom']} …", end=" ", flush=True)
    try:
        page.goto(comp["url"], wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"ÉCHEC ouverture ({e})"); return None
    _fermer_cookies(page)
    _attendre_matchs(page, 30)

    if os.environ.get("LNH_DEBUG"):
        try:
            slug = re.sub(r"[^a-z0-9]+", "_", comp["nom"].lower())
            with open(os.path.join(ICI, "docs", f"_debug_{slug}.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
        except Exception:
            pass

    fusion = {}

    def absorber():
        for m in _extraire(page):
            fusion[m["id"]] = m

    absorber()  # ce qui est affiché par défaut

    # Repérer les listes déroulantes présentes
    try:
        selects = page.locator("select")
        n = selects.count()
    except Exception:
        n = 0

    sel_mois = lab_mois = None
    sel_jr = lab_jr = None
    for i in range(n):
        sel = selects.nth(i)
        labels = _labels_options(sel)
        low = " ".join(labels).lower()
        if any(mn in low for mn in _MOIS_NOMS):
            sel_mois, lab_mois = sel, labels
        elif "journée" in low or "journee" in low:
            sel_jr, lab_jr = sel, labels

    def _index_tout(labels, mots):
        for j, l in enumerate(labels):
            if any(m in l.lower() for m in mots):
                return j
        return None

    # 1) Parcourir TOUTES LES JOURNÉES (mois réglé sur « tous » pour ne pas gêner)
    if sel_jr:
        if sel_mois:
            k = _index_tout(lab_mois, ["tous"])
            if k is not None:
                _choisir(page, sel_mois, k)
        k = _index_tout(lab_jr, ["toutes", "tous"])
        if k is not None and _choisir(page, sel_jr, k):
            absorber()                              # « toutes les journées » d'un coup
        for j, lab in enumerate(lab_jr):
            ll = lab.lower()
            if "toute" in ll or "tous" in ll:
                continue
            if _choisir(page, sel_jr, j):           # chaque journée, une par une
                absorber()
        k = _index_tout(lab_jr, ["toutes", "tous"])  # remettre sur « toutes »
        if k is not None:
            _choisir(page, sel_jr, k)

    # 2) Parcourir TOUS LES MOIS (journées réglées sur « toutes »)
    if sel_mois:
        for j, lab in enumerate(lab_mois):
            ll = lab.lower()
            if "tous" in ll:
                continue
            if any(mn in ll for mn in _MOIS_NOMS):
                if _choisir(page, sel_mois, j):
                    absorber()

    matchs = list(fusion.values())
    print(f"{len(matchs)} matchs")
    return matchs


# --------------------------------------------------------------------------
# État + e-mail
# --------------------------------------------------------------------------

def charger_state():
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def sauver_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def envoyer_email(sujet, corps):
    import smtplib
    from email.mime.text import MIMEText
    user = os.environ.get("SMTP_USER"); pwd = os.environ.get("SMTP_PASS")
    dest = os.environ.get("MAIL_TO", user)
    if not (user and pwd and dest):
        print("  (e-mail non configuré — aucun envoi)"); return
    dests = [d.strip() for d in dest.split(",") if d.strip()]
    msg = MIMEText(corps, "plain", "utf-8")
    msg["Subject"] = sujet; msg["From"] = user; msg["To"] = ", ".join(dests)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=25) as s:
        s.starttls(); s.login(user, pwd); s.sendmail(user, dests, msg.as_string())
    print(f"  e-mail envoyé à {', '.join(dests)}")


# --------------------------------------------------------------------------

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright manquant : pip install playwright && playwright install chromium")
        sys.exit(1)

    horod = datetime.now().strftime("%d/%m/%Y à %H:%M")
    print(f"=== Vérification {horod} ===")
    state = charger_state()
    resultats = []
    total = 0

    with sync_playwright() as p:
        nav = p.chromium.launch(headless=True)
        ctx = nav.new_context(locale="fr-FR",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"))
        page = ctx.new_page()
        for comp in COMPETITIONS:
            nom = comp["nom"]
            anciens = state.get(nom, None)
            nouveaux = recuperer(page, comp)

            # --- Garde-fous anti fausse alerte ---
            if nouveaux is None:
                # échec réseau/lecture : on garde l'affichage précédent, aucune alerte
                affichage = anciens or []
                diff = core.diff_matchs(affichage, affichage)
            elif anciens is None:
                # première fois : on enregistre la référence, sans alerter
                state[nom] = nouveaux
                affichage = nouveaux
                diff = {"changements": [], "nouveaux": [], "supprimes": []}
                print("     (référence initiale enregistrée)")
            elif len(nouveaux) == 0 and len(anciens) > 0:
                # 0 match alors qu'on en avait : anomalie probable → on ne touche à rien
                affichage = anciens
                diff = core.diff_matchs(affichage, affichage)
                print("     (0 match reçu — ignoré pour éviter une fausse alerte)")
            else:
                diff = core.diff_matchs(anciens, nouveaux)
                state[nom] = nouveaux
                affichage = nouveaux

            resultats.append({"nom": nom, "url": comp["url"], "matchs": affichage, "diff": diff})
            n = core.nb_changements(diff)
            total += n
            if n:
                print(f"     >>> {n} changement(s) !")
        nav.close()

    # Page web
    os.makedirs(os.path.dirname(SITE), exist_ok=True)
    with open(SITE, "w", encoding="utf-8") as f:
        f.write(core.generer_html(resultats, datetime.now().strftime("%d/%m/%Y à %H:%M")))
    sauver_state(state)

    if total:
        mail = core.construire_email(resultats, os.environ.get("SITE_URL"))
        if mail:
            entete = f"\n===== {horod} — {total} changement(s) =====\n"
            os.makedirs(os.path.dirname(HISTO), exist_ok=True)
            with open(HISTO, "a", encoding="utf-8") as f:
                f.write(entete + mail[1] + "\n")
            try:
                envoyer_email(*mail)
            except Exception as e:
                print(f"  (échec e-mail : {e})")
        print(f"{total} changement(s) au total.")
    else:
        print("Aucun changement.")


if __name__ == "__main__":
    main()
