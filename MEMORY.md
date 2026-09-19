# MEMORY.md — Journal de mémoire du projet

Journal **append-only** : on n'efface ni ne réécrit les entrées passées, on ajoute une
nouvelle entrée datée à chaque session de travail importante. Ne doit **jamais** contenir de
clés, tokens ou secrets (voir `config/credentials/`).

Format d'entrée suggéré :

```
## AAAA-MM-JJ — Titre court

**Décisions techniques**
- ...

**État d'avancement par agent**
- Création de site : ...
- Réseaux sociaux : ...
- Maintenance : ...
- Prospection : ...

**Problèmes rencontrés / solutions**
- ...

**Questions ouvertes**
- ...
```

---

## 2026-09-19 — Kickoff du projet

**Décisions techniques**
- Positionnement validé : plateforme de digitalisation pour PME/indépendants en Afrique,
  pilotée par 4 agents IA (Création de site, Réseaux sociaux, Maintenance, Prospection
  commerciale), sur abonnement mensuel en 3 packs (Starter / Business / Premium). Le
  contenu détaillé de chaque pack reste à définir.
- Règles de sécurité et de permissions des agents actées et documentées dans `CLAUDE.md`
  (section 5) : cloisonnement strict entre agents, validation humaine obligatoire pour tout
  paiement/suppression de données, interdiction de contacter un prospect filtré comme non
  favorable/non joignable, interdiction de publier sans brief validé, aucune gestion de la
  clé API Claude par les agents, aucun secret committé dans le dépôt.
- Création de `CLAUDE.md` (référence projet) et de `MEMORY.md` (ce fichier).
- Choix conservateur : ne pas créer `config/credentials/` ni l'arborescence `agents/`
  avant d'avoir arrêté la stack technique, pour éviter de figer une structure qui ne
  correspondrait pas aux choix techniques réels.

**État d'avancement par agent**
- Création de site : non démarré.
- Réseaux sociaux : non démarré.
- Maintenance : non démarré.
- Prospection : non démarré.

**Problèmes rencontrés / solutions**
- Aucun à ce stade.

**Questions ouvertes**
- Détail des 3 packs d'abonnement (quels agents/quotas par pack).
- Framework frontend du dashboard client, hébergement/infrastructure de production.
- Voir aussi les "points à trancher avant implémentation" listés dans chaque
  `agents/<nom-agent>/skills/README.md`.

---

## 2026-09-19 — Stack technique et scaffolding initial

**Décisions techniques**
- Stack validée avec l'utilisateur : **Python** comme langage/runtime principal,
  **Claude Agent SDK** pour l'orchestration des 4 agents.
- Base de données : **PostgreSQL** (SQLAlchemy + Alembic), avec JSONB pour le contenu
  semi-structuré par agent — recommandation Claude, validée par l'utilisateur (choix
  délégué).
- Architecture du dépôt : **monorepo**, cloisonnement par dossier `agents/<nom-agent>/`
  plutôt que par dépôt séparé — recommandation Claude, validée par l'utilisateur (choix
  délégué).
- `CLAUDE.md` §3 et §6 mis à jour en conséquence.
- Création de `.gitignore` (secrets, Python, Node, OS/éditeurs).
- Création de `config/credentials/README.md` (liste des clés attendues par agent,
  clé API Claude explicitement exclue) et `config/credentials/.env.example` (gabarit
  vide). Le fichier `.env` réel n'a volontairement pas été créé : à copier et remplir par
  l'utilisateur lui-même.
- Création de l'arborescence `agents/<nom-agent>/skills/README.md` pour les 4 agents, avec
  pour chacun : skills/librairies retenues et justification, points encore à trancher,
  rappel des permissions spécifiques. Choix notables : Jinja2 + Tailwind pour la Création
  de site, Meta Graph API + WhatsApp Business API pour les Réseaux sociaux, Sentry +
  UptimeRobot pour la Maintenance, scoring par règles métier (plutôt que ML) + rappel de
  conformité légale (ToS, RGPD) pour la Prospection.

**État d'avancement par agent**
- Création de site : skills documentées, aucun code.
- Réseaux sociaux : skills documentées, aucun code.
- Maintenance : skills documentées, aucun code.
- Prospection : skills documentées, aucun code.

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Framework frontend du dashboard client, hébergement/infrastructure de production.
- Catalogue de templates par secteur (Création de site), sources publiques autorisées et
  critères de scoring (Prospection), format du brief/validation avant publication (Réseaux
  sociaux), politique de rétention des sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé, migrations) non démarré —
  prochaine étape une fois les points ci-dessus tranchés.

---

## 2026-09-19 — Détail des 3 packs d'abonnement

**Décisions techniques**
- `CLAUDE.md` §1 complété avec la table détaillée des 3 packs (agents inclus + quotas par
  pack). Logique retenue : montée en gamme progressive, chaque pack ajoute des agents/
  capacités plutôt que de simplement augmenter des quotas.
- Réseaux sociaux : absent du pack Starter, inclus en Business (2 réseaux, 12 posts/mois) et
  Premium (multi-réseaux + campagnes payantes, 30 posts/mois) — décision utilisateur.
- Prospection commerciale : absente du pack Starter, incluse en Business (20 fiches
  qualifiées/mois) et Premium (60 fiches qualifiées/mois, supports illimités) — décision
  utilisateur, justifiée par le coût d'opération de l'agent et son rôle de différenciateur
  pour les packs payants.
- Création de site et Maintenance : inclus dans les 3 packs dès le Starter, avec des
  capacités croissantes (pages, révisions, fréquence de monitoring/sauvegarde).
- Quotas chiffrés proposés par Claude comme base de travail (non validés sur des coûts API
  réels) : à ajuster une fois le pricing final et les coûts d'infrastructure connus.

**État d'avancement par agent**
- Inchangé (skills documentées pour les 4 agents, aucun code applicatif).

**Problèmes rencontrés / solutions**
- Une réponse utilisateur ambiguë sur le positionnement de la Prospection a nécessité une
  question de clarification supplémentaire avant de trancher.

**Questions ouvertes**
- Validation des quotas chiffrés une fois les coûts API réels (Meta, WhatsApp Business,
  scraping, etc.) et le pricing final connus.
- Hébergement/infrastructure de production.
- Catalogue de templates par secteur (Création de site), sources publiques autorisées et
  critères de scoring (Prospection), format du brief/validation avant publication (Réseaux
  sociaux), politique de rétention des sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé, migrations) non démarré.

---

## 2026-09-19 — Framework web/API et dashboard client

**Décisions techniques**
- Choix délégué par l'utilisateur ; tranché par Claude : stack **100% Python** pour rester
  cohérent avec le reste du projet et adapté à une petite équipe + utilisateurs
  majoritairement mobiles avec connectivité parfois limitée (marché cible africain).
- **FastAPI** retenu comme framework web/API (async, léger, adapté à l'orchestration des
  agents via Claude Agent SDK, documentation OpenAPI automatique).
- **Dashboard client** rendu côté serveur : Jinja2 (déjà utilisé par l'agent Création de
  site) + HTMX (interactivité sans rechargement complet) + Alpine.js (interactions
  ponctuelles côté client) + Tailwind CSS (cohérent avec le style des sites générés).
- Alternative écartée pour l'instant : un frontend SPA séparé (Next.js/Nuxt) — plus riche en
  interactions mais double la stack à maintenir (Python + JS) et alourdit le poids de page
  pour des utilisateurs mobiles en connectivité parfois limitée. À reconsidérer si le
  dashboard doit devenir très interactif en temps réel.
- `CLAUDE.md` §3 mis à jour ; retiré de la liste "encore à trancher".

**État d'avancement par agent**
- Inchangé (skills documentées pour les 4 agents, aucun code applicatif).

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Approche technique précise de génération de site (catalogue de templates par secteur).
- Sources publiques autorisées et critères de scoring (Prospection), format du
  brief/validation avant publication (Réseaux sociaux), politique de rétention des
  sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé, migrations) non démarré.

---

## 2026-09-19 — Hébergement de production

**Décisions techniques**
- **Fly.io** retenu pour héberger l'app (FastAPI + dashboard) et PostgreSQL managé —
  choix utilisateur parmi les options recommandées. Critère décisif : région Afrique du Sud
  (Johannesburg) qui réduit la latence pour les utilisateurs cibles, déploiement Docker
  simple, coût maîtrisé pour une petite équipe.
- **Cloudflare (R2 + CDN)** retenu pour le stockage objet (sites clients générés, backups)
  et leur diffusion — choix utilisateur. Critère décisif : nombreux points de présence en
  Afrique, pas de frais de sortie (egress) sur R2.
- Alternatives écartées : AWS af-south-1 (trop complexe/coûteux pour le stade actuel),
  Render/DigitalOcean (pas de région africaine).
- `CLAUDE.md` §3 mis à jour ; toutes les décisions de stack de la section 3 sont désormais
  actées, hors approche technique précise de génération de site.
- `config/credentials/README.md` et `.env.example` mis à jour : ajout de `FLY_API_TOKEN`
  (infrastructure/CI-CD, pas un agent métier) et des variables Cloudflare R2
  (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_R2_ACCESS_KEY_ID`,
  `CLOUDFLARE_R2_SECRET_ACCESS_KEY`, `CLOUDFLARE_R2_BUCKET`), en remplacement de l'ancien
  `BACKUP_STORAGE_KEY` générique.

**État d'avancement par agent**
- Inchangé (skills documentées pour les 4 agents, aucun code applicatif).

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Approche technique précise de génération de site (catalogue de templates par secteur).
- Sources publiques autorisées et critères de scoring (Prospection), format du
  brief/validation avant publication (Réseaux sociaux), politique de rétention des
  sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé FastAPI, migrations Alembic,
  Dockerfile pour Fly.io) non démarré — c'est la prochaine étape naturelle, toute la stack
  étant maintenant fixée.

---

## 2026-09-19 — Catalogue de templates par secteur (agent Création de site)

**Décisions techniques**
- Catalogue MVP fixé à **9 secteurs + 1 template générique de repli**, documenté dans
  `agents/creation-site/skills/README.md` : Restaurant/restauration rapide, Boutique/
  commerce de détail, Services beauté & bien-être, Artisanat & métiers techniques,
  Services professionnels/conseil, Santé, Hôtellerie & tourisme, Éducation & formation,
  Événementiel, et un template générique pour tout secteur non couvert.
- 6 secteurs de base proposés par Claude ; 3 secteurs additionnels (Hôtellerie & tourisme,
  Éducation & formation, Événementiel) ajoutés au MVP sur validation explicite de
  l'utilisateur.
- Structure commune définie pour tous les templates : header, hero, section(s) spécifiques
  au secteur, section Contact, footer.
- Contrainte spécifique actée pour le secteur Santé : aucun contenu médical généré sans
  validation par un professionnel de santé du client.
- Secteurs volontairement exclus du MVP (agriculture/agroalimentaire, ONG/associations,
  etc.) : couverts par le template générique en attendant une demande réelle.
- Mode de publication des sites tranché par ricochet de la décision d'hébergement : stockage
  statique sur Cloudflare R2 + CDN (CLAUDE.md §3). Reste ouvert : générer 100% statique au
  build, ou garder certaines sections semi-dynamiques servies par FastAPI (ex. formulaire de
  réservation).
- `CLAUDE.md` §3 mis à jour : toutes les décisions de stack sont désormais actées.

**État d'avancement par agent**
- Création de site : catalogue de templates et stack techniques actés, aucun code.
- Autres agents : inchangé.

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Génération 100% statique vs sections semi-dynamiques pour les sites clients (Création de
  site).
- Mécanisme de prévisualisation/validation du site par le client avant mise en ligne.
- Sources publiques autorisées et critères de scoring (Prospection), format du
  brief/validation avant publication (Réseaux sociaux), politique de rétention des
  sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé FastAPI, migrations Alembic,
  Dockerfile pour Fly.io) non démarré.

---

## 2026-09-19 — Pays de lancement (Gabon) et scalabilité multi-pays

**Décisions techniques**
- Pays de lancement confirmé par l'utilisateur : **Gabon**, avec objectif explicite de
  scaler vers d'autres pays africains ensuite. `CLAUDE.md` §1 complété avec une section
  "Pays de lancement et scalabilité multi-pays" listant les implications concrètes
  (paiement, devise, langue, conformité) à respecter dès l'implémentation pour ne pas
  bloquer l'extension future.
- Correction de la liste des moyens de paiement : **MTN n'opère pas au Gabon** et la
  présence de **Wave** n'y est pas confirmée (surtout présent en Afrique de l'Ouest).
  Ajout de `AIRTEL_MONEY_API_KEY` et `MOOV_MONEY_API_KEY` (opérateurs réellement présents
  au Gabon, avec Orange Money) dans `config/credentials/README.md` et `.env.example`.
  `MTN_MOMO_API_KEY`/`WAVE_API_KEY` conservés mais marqués "réservés" pour une future
  extension vers des pays où ces opérateurs sont présents, plutôt que supprimés.
- Principe posé pour la suite : moyens de paiement, devise et conformité légale doivent être
  **paramétrables par pays** dans le modèle de données/l'architecture, pas codés en dur pour
  un seul pays — à respecter dès le scaffolding applicatif (ex. champ pays/devise sur le
  client, sélection des providers de paiement actifs par pays).
- Le français reste la langue par défaut adaptée au Gabon et à l'Afrique francophone ; le
  multilingue est noté comme besoin futur (pays anglophones/lusophones), non requis pour le
  lancement mais à ne pas bloquer par du texte codé en dur dans le code applicatif.

**État d'avancement par agent**
- Inchangé (aucun code applicatif).

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Génération 100% statique vs sections semi-dynamiques pour les sites clients (Création de
  site).
- Mécanisme de prévisualisation/validation du site par le client avant mise en ligne.
- Sources publiques autorisées et critères de scoring (Prospection), format du
  brief/validation avant publication (Réseaux sociaux), politique de rétention des
  sauvegardes (Maintenance).
- Confirmer précisément les conditions d'intégration Airtel Money/Moov Money Gabon
  (documentation API, éligibilité marchande) avant implémentation.
- Scaffolding applicatif réel (pyproject.toml, package partagé FastAPI, migrations Alembic,
  Dockerfile pour Fly.io) non démarré.
