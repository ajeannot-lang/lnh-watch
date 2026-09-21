# 🟢 Tuto tout simple — installation en 6 étapes (~15 min, une seule fois)

But : avoir **un lien à partager** (toujours à jour, changements en rouge) **+ un mail
automatique** quand un horaire bouge. Les gestionnaires n'installeront **rien**.

Tu fais ça **une seule fois**. Après, c'est automatique pour toujours.

---

## Étape 1 — Créer un compte (2 min)
Va sur **github.com** → bouton **Sign up** → mets un mail + un mot de passe.
(Déjà un compte ? Connecte-toi, saute cette étape.)

## Étape 2 — Créer le projet (1 min)
En haut à droite, clique le **+** → **New repository**.
Dans « Repository name » écris : **lnh-watch**. Laisse le reste tel quel.
Descends, clique le bouton vert **Create repository**.

## Étape 3 — Déposer mes fichiers (2 min)
Sur la page qui s'ouvre, clique **uploading an existing file** (lien bleu au milieu).
Sur ton ordi, **décompresse** `lnh-watch.zip` (clic droit → Extraire).
**Glisse tout le contenu** du dossier décompressé dans la fenêtre GitHub.
En bas, clique le bouton vert **Commit changes**.

## Étape 4 — Brancher ton mail (5 min)
En haut, clique **Settings** (l'engrenage) → à gauche **Secrets and variables** →
**Actions** → bouton **New repository secret**. Tu crées **3 secrets** (un par un) :

1. Name : `SMTP_USER` — Secret : ton adresse Gmail
2. Name : `SMTP_PASS` — Secret : ton **mot de passe d'application** Gmail *(voir plus bas)*
3. Name : `MAIL_TO` — Secret : les mails à prévenir, séparés par des virgules
   (toi + les gestionnaires)

> **Mot de passe d'application Gmail** (2 min) : va sur **myaccount.google.com** →
> **Sécurité** → active la **validation en 2 étapes** → puis cherche **« Mots de passe
> des applications »** → crée-en un → copie les 16 lettres → colle-les dans `SMTP_PASS`.
> ⚠️ Ce n'est **pas** ton mot de passe Gmail habituel.

## Étape 5 — Allumer la page web (2 min)
Toujours dans **Settings** → à gauche **Pages**.
Sous « Branch », choisis **main** et le dossier **/docs** → clique **Save**.
Attends 1 min, rafraîchis : GitHub affiche ton lien, du style
**https://ton-pseudo.github.io/lnh-watch/** → **c'est le lien à partager.**

## Étape 6 — Lancer une première fois (1 min)
En haut, clique **Actions** → clique **« Surveillance calendriers LNH »** à gauche →
bouton **Run workflow** → **Run workflow**.
Attends 2 min, ouvre ton lien : la page se remplit toute seule. 🎉

---

## Et après ?
- Le **lien** est toujours à jour tout seul (vérif chaque heure). Partage-le, mets-le en favori.
- Un **mail** part automatiquement **seulement** quand un horaire change.
- Pour ajouter/enlever un destinataire : Settings → Secrets → modifie `MAIL_TO`.

## Un souci ? (envoie-moi ça, je corrige)
- Un mois ou une journée qui manque : Settings → Secrets → ajoute `LNH_DEBUG` = `1`,
  relance (Actions → Run workflow), ouvre `ton-lien/_debug_daikin_starligue.html`
  et envoie-le-moi. (Enlève `LNH_DEBUG` après.)
- Pas de mail reçu : re-vérifie `SMTP_PASS` (mot de passe **d'application**) + les spams.

Bloqué à une étape ? Dis-moi juste **le numéro de l'étape**, je te débloque.
