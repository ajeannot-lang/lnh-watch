# -*- coding: utf-8 -*-
"""
lnh_core.py — Cœur : comparaison de calendriers + génération de la page web
+ texte de l'e-mail. Aucune dépendance, aucun accès réseau.
"""

import html
import re
from datetime import datetime

_MOIS = {"janv":1,"févr":2,"fevr":2,"mars":3,"avr":4,"mai":5,"juin":6,
         "juil":7,"août":8,"aout":8,"sept":9,"oct":10,"nov":11,"déc":12,"dec":12}


def parse_horaire(schedule_text, saison_debut=None):
    if not schedule_text:
        return None
    t = schedule_text.lower()
    m = re.search(r"(\d{1,2})\s*([a-zéûôàè]+)\.?", t)
    if not m:
        return None
    jour = int(m.group(1)); mois_txt = m.group(2)[:4]; mois = None
    for cle, val in _MOIS.items():
        if mois_txt.startswith(cle[:4]):
            mois = val; break
    if mois is None:
        return None
    hm = re.search(r"(\d{1,2})\s*h\s*(\d{2})?", t)
    heure = int(hm.group(1)) if hm else 0
    minute = int(hm.group(2)) if (hm and hm.group(2)) else 0
    if saison_debut is None:
        n = datetime.now()
        saison_debut = n.year if n.month >= 7 else n.year - 1
    annee = saison_debut if mois >= 7 else saison_debut + 1
    try:
        return datetime(annee, mois, jour, heure, minute)
    except ValueError:
        return None


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def diff_matchs(anciens, nouveaux):
    """Compare deux listes de matchs (clé stable = 'id'). Détecte les
    changements d'horaire, les nouveaux matchs et les matchs retirés."""
    ia = {m["id"]: m for m in anciens}
    inw = {m["id"]: m for m in nouveaux}
    changements, nouv, suppr = [], [], []
    for mid, m in inw.items():
        if mid not in ia:
            nouv.append(m)
        elif _norm(ia[mid].get("horaire", "")) != _norm(m.get("horaire", "")):
            changements.append({"id": mid, "match": m.get("match", ""),
                                "journee": m.get("journee", ""),
                                "avant": ia[mid].get("horaire", ""),
                                "apres": m.get("horaire", "")})
    for mid, m in ia.items():
        if mid not in inw:
            suppr.append(m)
    return {"changements": changements, "nouveaux": nouv, "supprimes": suppr}


def nb_changements(diff):
    return len(diff["changements"]) + len(diff["nouveaux"]) + len(diff["supprimes"])


# --- E-mail (texte simple, lisible partout) -------------------------------

def construire_email(resultats, url_site=None):
    total = sum(nb_changements(c["diff"]) for c in resultats)
    if not total:
        return None
    lignes = [f"{total} changement(s) détecté(s) sur les calendriers LNH :", ""]
    for c in resultats:
        d = c["diff"]
        if not nb_changements(d):
            continue
        lignes.append(f"— {c['nom']} —")
        for ch in d["changements"]:
            lignes.append(f"  • HORAIRE  {ch['journee']}  {ch['match']}")
            lignes.append(f"             {ch['avant']}   →   {ch['apres']}")
        for m in d["nouveaux"]:
            lignes.append(f"  • NOUVEAU  {m.get('journee','')}  {m.get('match','')}  ({m.get('horaire','')})")
        for m in d["supprimes"]:
            lignes.append(f"  • RETIRÉ   {m.get('journee','')}  {m.get('match','')}  ({m.get('horaire','')})")
        lignes.append("")
    if url_site:
        lignes.append(f"Calendrier complet à jour : {url_site}")
    lignes.append("")
    lignes.append("(Message automatique — surveillance des calendriers lnh.fr)")
    sujet = f"[LNH] {total} changement(s) de calendrier"
    return sujet, "\n".join(lignes)


# --- Page web (dashboard) -------------------------------------------------

_CSS = """
:root{--bg:#0f1420;--card:#171d2b;--line:#263049;--txt:#e7ecf5;--muted:#8a97b1;
--rouge:#ff4d4f;--rouge-bg:#3a1416;--vert:#3ddc84;--vert-bg:#123322;--gris:#6b7690;--accent:#e30613;}
@media(prefers-color-scheme:light){:root{--bg:#f4f6fb;--card:#fff;--line:#e2e7f0;--txt:#141a26;
--muted:#5b6478;--rouge:#d40000;--rouge-bg:#ffe9e9;--vert:#0a8f47;--vert-bg:#e6f7ee;--gris:#8a94a8;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:20px 16px 60px}
header.top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}
header.top h1{font-size:20px;margin:0;font-weight:800}
.badge{background:var(--accent);color:#fff;border-radius:6px;padding:2px 8px;font-size:12px;font-weight:700}
.maj{color:var(--muted);font-size:13px;margin:2px 0 18px}
.alerte{border:1px solid var(--rouge);background:var(--rouge-bg);border-radius:12px;padding:14px 16px;margin:0 0 22px}
.alerte h2{margin:0 0 8px;font-size:15px;color:var(--rouge)}
.alerte ul{margin:0;padding-left:18px}.alerte li{margin:4px 0;font-size:14px}
.alerte .flch{color:var(--rouge);font-weight:700}
.rien{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:14px 16px;margin:0 0 22px;color:var(--muted);font-size:14px}
section.comp{margin:0 0 26px}
section.comp h2{font-size:16px;margin:0 0 10px;padding-bottom:6px;border-bottom:2px solid var(--accent)}
section.comp h2 a{color:inherit;text-decoration:none}
section.comp h2 .src{font-weight:400;color:var(--muted);font-size:12px}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;border:1px solid var(--line);font-size:14px}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:rgba(127,127,127,.08);font-weight:700;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
tr:last-child td{border-bottom:none}
td.jr{white-space:nowrap;color:var(--muted);width:70px}
td.horaire{white-space:nowrap;font-variant-numeric:tabular-nums}
.tag{display:inline-block;font-size:11px;font-weight:700;border-radius:5px;padding:1px 7px;margin-left:6px}
tr.chg{background:var(--rouge-bg)}tr.chg td.horaire{color:var(--rouge);font-weight:700}
tr.chg .avant{color:var(--muted);text-decoration:line-through;font-weight:400}
tr.chg .flch{color:var(--rouge);font-weight:700;padding:0 4px}.tag.chg{background:var(--rouge);color:#fff}
tr.new{background:var(--vert-bg)}.tag.new{background:var(--vert);color:#04210f}
tr.sup td{color:var(--gris);text-decoration:line-through}.tag.sup{background:var(--gris);color:#fff;text-decoration:none}
.vide{color:var(--muted);font-style:italic;padding:12px}
td.diff{white-space:nowrap}
.dfx{display:inline-block;font-size:11px;font-weight:700;border-radius:5px;padding:1px 7px;margin-right:4px}
.dfx-htv{background:#e30613;color:#fff}
.dfx-bein{background:#5b2a86;color:#fff}
.dfx-x{background:transparent;color:var(--muted);font-weight:400}
.ac{color:var(--muted);font-style:italic;font-size:12px}
footer{color:var(--muted);font-size:12px;text-align:center;margin-top:30px}
"""


def _esc(s):
    return html.escape(s or "")


def _horaire_html(s):
    """Affiche l'horaire ; met « (à confirmer) » en gris italique."""
    s = s or ""
    if "(à confirmer)" in s:
        base = _esc(s.replace("(à confirmer)", "").strip())
        return f'{base} <span class="ac">(à confirmer)</span>'
    return _esc(s)


def _diffuseur_html(d):
    """Petit badge coloré selon le diffuseur."""
    if not d:
        return '<span class="dfx dfx-x">—</span>'
    dl = d.lower()
    if "handball tv" in dl and "bein" in dl:
        return ('<span class="dfx dfx-htv">Handball TV</span>'
                '<span class="dfx dfx-bein">beIN</span>')
    if "handball tv" in dl:
        return '<span class="dfx dfx-htv">Handball TV</span>'
    if "bein" in dl:
        return '<span class="dfx dfx-bein">beIN SPORTS</span>'
    return f'<span class="dfx dfx-x">{_esc(d)}</span>'


def generer_html(competitions, maj_horodatage=None):
    maj = maj_horodatage or datetime.now().strftime("%d/%m/%Y à %H:%M")
    total = sum(nb_changements(c["diff"]) for c in competitions)

    if total == 0:
        alerte = ('<div class="rien">✓ Aucun changement depuis la dernière '
                  'vérification. Tous les horaires sont identiques.</div>')
    else:
        items = []
        for c in competitions:
            d = c["diff"]
            for ch in d["changements"]:
                items.append(f'<li><b>{_esc(c["nom"])}</b> — {_esc(ch["journee"])} — '
                             f'{_esc(ch["match"])} : <span class="avant">{_esc(ch["avant"])}</span>'
                             f'<span class="flch"> → </span><b>{_esc(ch["apres"])}</b></li>')
            for m in d["nouveaux"]:
                items.append(f'<li><b>{_esc(c["nom"])}</b> — nouveau match : '
                             f'{_esc(m.get("match",""))} ({_esc(m.get("horaire",""))})</li>')
            for m in d["supprimes"]:
                items.append(f'<li><b>{_esc(c["nom"])}</b> — match retiré : '
                             f'{_esc(m.get("match",""))} ({_esc(m.get("horaire",""))})</li>')
        alerte = (f'<div class="alerte"><h2>⚠ {total} changement(s) détecté(s) '
                  f'depuis la dernière vérification</h2><ul>{"".join(items)}</ul></div>')

    sections = []
    for c in competitions:
        d = c["diff"]
        ids_chg = {x["id"]: x for x in d["changements"]}
        ids_new = {m["id"] for m in d["nouveaux"]}
        lignes = []
        matchs = sorted(c["matchs"], key=lambda m: (parse_horaire(m.get("horaire","")) or datetime.max))
        for m in matchs:
            classe, tag = "", ""
            if m["id"] in ids_chg:
                classe = "chg"; tag = '<span class="tag chg">HORAIRE MODIFIÉ</span>'
                horaire_cell = (f'<span class="avant">{_horaire_html(ids_chg[m["id"]]["avant"])}</span>'
                                f'<span class="flch">→</span>{_horaire_html(ids_chg[m["id"]]["apres"])}')
            elif m["id"] in ids_new:
                classe = "new"; tag = '<span class="tag new">NOUVEAU</span>'
                horaire_cell = _horaire_html(m.get("horaire",""))
            else:
                horaire_cell = _horaire_html(m.get("horaire",""))
            lignes.append(f'<tr class="{classe}"><td class="jr">{_esc(m.get("journee",""))}</td>'
                          f'<td>{_esc(m.get("match",""))}{tag}</td>'
                          f'<td class="horaire">{horaire_cell}</td>'
                          f'<td class="diff">{_diffuseur_html(m.get("diffuseur",""))}</td></tr>')
        for m in d["supprimes"]:
            lignes.append(f'<tr class="sup"><td class="jr">{_esc(m.get("journee",""))}</td>'
                          f'<td>{_esc(m.get("match",""))}<span class="tag sup">RETIRÉ</span></td>'
                          f'<td class="horaire">{_horaire_html(m.get("horaire",""))}</td>'
                          f'<td class="diff">{_diffuseur_html(m.get("diffuseur",""))}</td></tr>')
        corps = "".join(lignes) if lignes else '<tr><td colspan="4" class="vide">Aucun match récupéré.</td></tr>'
        titre = _esc(c["nom"])
        if c.get("url"):
            titre = f'<a href="{_esc(c["url"])}" target="_blank" rel="noopener">{titre}</a>'
        src = (f' <span class="src">({len(c["matchs"])} matchs · voir sur lnh.fr ↗)</span>'
               if c.get("url") else f' <span class="src">({len(c["matchs"])} matchs)</span>')
        sections.append(f'<section class="comp"><h2>{titre}{src}</h2>'
                        f'<table><thead><tr><th>J.</th><th>Match</th><th>Date &amp; horaire</th>'
                        f'<th>Diffuseur</th></tr></thead>'
                        f'<tbody>{corps}</tbody></table></section>')

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Calendriers LNH — suivi des changements</title><style>{_CSS}</style></head>
<body><div class="wrap">
<header class="top"><span class="badge">LNH</span><h1>Calendriers — suivi des changements</h1></header>
<div class="maj">Dernière vérification automatique : {_esc(maj)}</div>
{alerte}
{''.join(sections)}
<footer>Mise à jour automatique toutes les heures — données © Ligue Nationale de Handball (lnh.fr).<br>
Les changements sont calculés par rapport à la vérification précédente.</footer>
</div></body></html>"""
