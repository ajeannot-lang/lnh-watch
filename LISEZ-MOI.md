# Surveillance des calendriers LNH — version automatique (cloud)

Ce dossier met en place, **gratuitement et sans rien laisser tourner sur ton PC** :

- une **page web unique, toujours à jour** (les 5 calendriers : StarLigue, ProLigue,
  Coupe de France, Ligue des Champions, Ligue Européenne — **toute la saison**, le robot
  parcourt automatiquement toutes les journées et tous les mois) où **les changements
  d'horaire ressortent en ROUGE** ;
- un **e-mail automatique** envoyé dès qu'un horaire de match change.

Un robot vérifie le site **toutes les heures**, met la page à jour et envoie le mail.
Toi, tu partages juste **un lien** aux gestionnaires et au planning — **ils n'installent rien**.

👉 Ouvre `apercu_page_partagee.html` pour voir à quoi ressemble la page.

---

## Installation (à faire UNE seule fois, ~15 min)

### 1. Créer un compte GitHub (gratuit)
Va sur https://github.com → **Sign up**. (Si tu en as déjà un, connecte-toi.)

### 2. Créer le projet
- Clique **+** (en haut à droite) → **New repository**.
- Nom : par exemple `lnh-watch`. Laisse **Public**. Clique **Create repository**.

### 3. Déposer les fichiers
- Sur la page du dépôt : **Add file → Upload files**.
- **Décompresse** le fichier `lnh-watch.zip` que je t'ai donné, puis **glisse tout son
  contenu** dans la fenêtre (garde bien le dossier `.github`).
- En bas, clique **Commit changes**.

### 4. Régler l'e-mail (les alertes)
- Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**.
- Crée ces secrets (bouton à chaque fois) :

  | Nom | Valeur |
  |---|---|
  | `SMTP_USER` | ton adresse Gmail (ex. `andre.jeannotpro@gmail.com`) |
  | `SMTP_PASS` | un **mot de passe d'application** Gmail (voir encadré) |
  | `MAIL_TO` | les destinataires, séparés par des virgules (toi + les gestionnaires) |

  > **Mot de passe d'application Gmail** : Compte Google → **Sécurité** → active la
  > **validation en 2 étapes**, puis **Mots de passe des applications** → crée-en un,
  > et colle les 16 caractères dans `SMTP_PASS`. Ce n'est pas ton mot de passe habituel.
  > (Avec une autre messagerie qu'Gmail, ajoute aussi `SMTP_HOST` et `SMTP_PORT`.)

### 5. Activer la page web
- **Settings → Pages** → sous *Build and deployment*, **Source : Deploy from a branch**,
  **Branch : `main`**, dossier **`/docs`** → **Save**.
- Au bout d'1-2 min, GitHub affiche l'adresse de ta page, du type :
  `https://TON-PSEUDO.github.io/lnh-watch/` → **c'est le lien à partager.**
- (Optionnel) reviens dans les secrets et ajoute `SITE_URL` = ce lien, pour qu'il
  apparaisse dans les e-mails.

### 6. Premier lancement
- Onglet **Actions** → clique le workflow **« Surveillance calendriers LNH »** →
  **Run workflow**. Après ~2 min, la page se remplit toute seule.

C'est fini. Ensuite, tout est **automatique**.

---

## Au quotidien

- **La page** (le lien de l'étape 5) est toujours à jour : partage-la, mets-la en favori.
- **Les mails** partent tout seuls, **uniquement** quand un horaire change.
- Pour **ajouter/retirer un destinataire** : modifie le secret `MAIL_TO`.

---

## Modifier les compétitions suivies

Ouvre `scraper.py`, en haut la liste `COMPETITIONS`. Tu peux ajouter une ligne, ex.
Trophée des Champions :
```
{"nom": "Trophée des Champions", "url": "https://www.lnh.fr/autres-competitions/trophees-des-champions"},
```
Commit → le robot la prendra en compte au prochain passage.

---

## En cas de souci

- **Il manque des mois / peu de matchs** : le robot parcourt normalement **tous les
  mois** de chaque compétition automatiquement. Si tu vois qu'il en manque, ajoute
  temporairement un secret `LNH_DEBUG` = `1`, relance (**Actions → Run workflow**), puis
  ouvre `TON-LIEN/_debug_daikin_starligue.html` (et les autres `_debug_...`) et
  envoie-les-moi : j'ajuste la lecture des listes déroulantes en quelques minutes.
  Pense à retirer le secret `LNH_DEBUG` ensuite.
- **Une compétition affiche « Aucun match »** durablement : possible en intersaison,
  ou le site a changé. Ouvre le journal d'exécution (**Actions** → le passage → l'étape
  « Vérifier les calendriers ») et envoie-moi ce qui s'affiche.
- **Je ne reçois pas les mails** : vérifie les secrets `SMTP_USER` / `SMTP_PASS` (mot
  de passe **d'application**, pas le mot de passe normal) et le dossier spam.
- **Rappel** : le robot ne « crie » jamais au changement lors du tout premier passage
  (il enregistre d'abord la référence), ni si le site répond mal (pas de fausse alerte).

---

### Comment ça marche (en bref)
Chaque match est reconnu par son lien sur lnh.fr (équipes + journée), qui ne change pas
même quand la LNH décale la rencontre. Le robot compare l'horaire d'aujourd'hui avec
celui d'hier : différent = changement, affiché en rouge et envoyé par mail.
