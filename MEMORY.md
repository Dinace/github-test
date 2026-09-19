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
- Hébergement/infrastructure de production.
- Approche technique précise de génération de site (catalogue de templates par secteur).
- Sources publiques autorisées et critères de scoring (Prospection), format du
  brief/validation avant publication (Réseaux sociaux), politique de rétention des
  sauvegardes (Maintenance).
- Scaffolding applicatif réel (pyproject.toml, package partagé, migrations) non démarré.
