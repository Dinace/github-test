# CLAUDE.md — Plateforme de digitalisation pour PME/indépendants (Afrique)

Ce document est la référence pour tout agent IA (Claude Code ou autre) intervenant sur ce
projet. Il doit être lu en entier avant toute intervention. Voir aussi `MEMORY.md` pour
l'historique des décisions et l'état d'avancement.

## 1. Description et positionnement

La plateforme permet à des **PME et indépendants en Afrique** de digitaliser leur activité
via un pilotage par agents IA, sur abonnement mensuel décliné en **3 packs** :

- **Starter**
- **Business**
- **Premium**

### Pays de lancement et scalabilité multi-pays

**Pays de lancement : Gabon.** L'objectif est de pouvoir étendre la plateforme à d'autres
pays africains ensuite, donc les décisions ci-dessous sont prises pour rester valables au
Gabon dès le lancement tout en restant extensibles, plutôt que de figer des choix
spécifiques à un seul pays dans le code ou la donnée.

Implications concrètes à respecter dans toute implémentation :
- **Moyens de paiement** : paramétrables par pays, pas une liste fixe pour toute la
  plateforme. Au Gabon : Orange Money, Airtel Money, Moov Money. MTN Mobile Money et Wave
  sont documentés dans `config/credentials/` mais réservés à de futurs pays où ils opèrent
  (MTN n'est pas présent au Gabon ; Wave y est non confirmé).
- **Devise** : le Gabon utilise le FCFA (XAF). Le pricing/la facturation doivent prévoir un
  champ devise par pays/client dès le modèle de données, pas une devise codée en dur.
- **Langue** : le français convient au Gabon et à une large partie de l'Afrique francophone
  (Ouest et Centre) ; l'extension vers des pays anglophones ou lusophones nécessitera une
  gestion multilingue (contenu généré et dashboard) — non requise pour le lancement, mais à
  ne pas bloquer par des chaînes de caractères codées en dur dans le code applicatif.
- **Conformité légale** (agent Prospection notamment) : les règles de protection des
  données diffèrent par pays (au Gabon, autorité de référence : CNPDCP). Les textes de
  conformité doivent être paramétrables par pays plutôt qu'un texte générique "Afrique".

### Détail des packs

Logique de montée en gamme progressive : chaque pack ajoute des agents et des capacités, pas
seulement des quotas plus élevés. Les quotas chiffrés ci-dessous sont une **base de travail**,
à ajuster une fois le coût réel des API tierces et le pricing final connus.

| | **Starter** | **Business** | **Premium** |
|---|---|---|---|
| **Création de site** | 1 site vitrine, template sectoriel, jusqu'à 5 pages, 2 révisions/mois | 1 site, jusqu'à 10 pages, révisions illimitées, intégration Google Business Profile | Site complet, pages illimitées, révisions illimitées, intégrations avancées (Google Business Profile + Ads) |
| **Réseaux sociaux** | Non inclus | Génération de contenu + calendrier, publication sur 2 réseaux (Meta + WhatsApp Business), jusqu'à 12 posts/mois | Publication multi-réseaux + campagnes payantes (Meta Ads, Google Ads), jusqu'à 30 posts/mois |
| **Maintenance** | Monitoring de disponibilité (vérification toutes les 30 min), sauvegarde mensuelle, alertes basiques | Monitoring (toutes les 5 min), sauvegardes hebdomadaires, scan de sécurité basique mensuel | Monitoring temps réel, sauvegardes quotidiennes, scan de sécurité hebdomadaire, support prioritaire |
| **Prospection commerciale** | Non inclus | 20 fiches prospect qualifiées/mois, scoring inclus, 1 support visuel d'offre/mois | 60 fiches prospect qualifiées/mois, scoring avancé, supports visuels d'offre illimités |

Décisions actées avec l'utilisateur :
- Réseaux sociaux : absent du Starter (argument de montée en gamme vers Business).
- Prospection commerciale : absente du Starter, incluse en Business et Premium — c'est
  l'agent le plus coûteux à opérer (recherche externe, scoring, conformité légale) et le
  plus central pour aider les clients à trouver des clients, d'où son rôle de
  différenciateur pour les packs payants supérieurs plutôt qu'un accès dilué dès l'entrée
  de gamme.
- Quotas validés du point de vue du coût **API Claude** (négligeable, < 1 $/mois/client
  même sur Premium — voir `docs/pricing-model.md`). Restent à valider : coût WhatsApp
  Business API au Gabon, coût Google Places API si utilisée par l'agent Prospection, et le
  prix d'abonnement final par pack (décision commerciale, voir `docs/pricing-model.md`).

## 2. Les 4 agents de la plateforme

| Agent | Rôle |
|---|---|
| **Création de site** | Génère un site web pour le client à partir d'un brief (secteur d'activité, contenu, identité visuelle), en s'appuyant sur des templates par secteur. |
| **Réseaux sociaux** | Génère du contenu (textes, visuels), planifie un calendrier de publication, et publie via les API des réseaux sociaux (Meta, WhatsApp Business) — uniquement sur validation préalable d'un brief ou d'un contenu. |
| **Maintenance** | Surveille les sites/comptes clients : monitoring, sauvegardes, sécurité, détection de bugs/anomalies. |
| **Prospection commerciale** | Recherche des prospects sur des supports publics, crée des fiches prospect, applique un scoring/filtrage, génère des supports visuels d'offre. |

Chaque agent a un périmètre de données et de code strictement cloisonné (voir section 5).
L'arborescence est :

```
agents/
  creation_site/skills/README.md
  reseaux_sociaux/skills/README.md
  maintenance/skills/README.md
  prospection/skills/README.md
```

Noms de dossiers en snake_case (et non kebab-case comme dans les premières versions de ce
document) : ce sont aussi des packages Python valides, importables directement (ex.
`agents.creation_site`).

`agents/creation_site/` contient désormais aussi du code (premier agent implémenté — voir
`agents/creation_site/skills/README.md` section "Implémentation actuelle"). Les 3 autres
agents n'ont encore que leur `skills/README.md` (conception, pas de code).

Chaque `skills/README.md` documente les skills/frameworks/librairies retenus pour l'agent
concerné, avec justification, points encore à trancher, et rappel des permissions qui lui
sont propres.

## 3. Stack technique

- **Langage/runtime principal** : Python.
- **Orchestration des agents IA** : pas un choix unique pour les 4 agents — à trancher par
  agent selon la forme réelle de sa tâche (voir `shared/agent-design.md`/tableau de décision
  du skill `claude-api` : un appel unique structuré n'a pas besoin du même outil qu'une
  exploration ouverte à plusieurs étapes). Pour l'agent Création de site : **API Claude
  directe** (SDK `anthropic`, un appel structuré brief → contenu JSON), pas le Claude Agent
  SDK — ce dernier donnerait un accès Bash/fichiers inutile et contraire au cloisonnement
  strict (section 5). Voir `agents/creation_site/skills/README.md` pour la justification
  complète. Les 3 autres agents n'ont pas encore leur code implémenté : le même arbitrage
  (API directe vs Agent SDK vs Tool Runner) est à refaire pour chacun au moment de
  l'implémenter, pas à supposer identique.
- **Base de données** : PostgreSQL (SQLAlchemy + Alembic pour les migrations), avec des
  colonnes JSONB pour le contenu semi-structuré et variable par agent (structure de site
  généré, contenu réseaux sociaux, champs libres de fiche prospect).
- **Architecture du dépôt** : monorepo. Un seul dépôt pour la plateforme et les 4 agents,
  avec un cloisonnement strict par dossier (`agents/<nom-agent>/`, voir section 2) plutôt
  que par dépôt séparé. Le code partagé entre agents (auth, facturation, accès base de
  données, mémoire commune) sera isolé dans un package partagé dédié le moment venu — pas
  encore créé à ce stade.
- **Framework web/API** : **FastAPI**. Async, léger, adapté pour exposer les actions des
  agents (Claude Agent SDK) côté serveur et documenter l'API automatiquement (OpenAPI).
- **Dashboard client** : rendu côté serveur, stack 100% Python plutôt qu'un frontend JS
  séparé.
  - **Jinja2** pour les templates (déjà utilisé par l'agent Création de site — une seule
    techno de templating dans tout le projet).
  - **HTMX** pour l'interactivité (rafraîchir une section de page sans rechargement complet)
    sans avoir à maintenir une stack JS/build séparée.
  - **Alpine.js** pour les interactions ponctuelles purement côté client (menus, toggles).
  - **Tailwind CSS** pour le style, cohérent avec le choix déjà fait pour les sites générés
    par l'agent Création de site.
  - Raison de ce choix : une seule équipe/langage à maintenir (Python de bout en bout),
    pages légères et rapides à charger — important vu l'usage majoritairement mobile et la
    connectivité parfois limitée dans le marché cible — et aucun build JS séparé à déployer.
    Limite assumée : moins adapté qu'un SPA (ex. Next.js) si le dashboard devait devenir
    très riche en interactions temps réel ; à réévaluer si ce besoin apparaît concrètement.

- **Hébergement/infrastructure de production** :
  - **Fly.io** pour l'app (FastAPI + dashboard) et PostgreSQL managé. Choisi pour sa région
    Afrique du Sud (Johannesburg) qui réduit la latence pour les utilisateurs africains,
    un déploiement simple (Docker) et un coût maîtrisé, adaptés à une petite équipe.
  - **Cloudflare (R2 + CDN)** pour le stockage objet (sites clients générés, backups,
    fichiers) et leur diffusion. Choisi pour ses nombreux points de présence en Afrique
    (rapproche les sites clients de leurs visiteurs) et l'absence de frais de sortie
    (egress) sur R2.
  - Alternatives écartées pour l'instant : AWS af-south-1 (plus puissant/scalable mais trop
    complexe et coûteux à opérer pour une petite équipe qui démarre) ; Render/DigitalOcean
    (très simples mais sans région africaine, donc latence plus élevée pour l'app elle-même
    sans CDN devant). À reconsidérer si le volume d'utilisateurs ou les besoins de montée en
    charge le justifient.

Toutes les décisions de stack sont désormais actées. Détail de la génération de site
(catalogue de templates par secteur, mode de publication) : voir
`agents/creation_site/skills/README.md`.

Le scaffolding applicatif existe (voir section 6) : `platform_core/` (config, DB, modèles),
`app/` (FastAPI + dashboard), `migrations/` (Alembic), `Dockerfile`/`fly.toml`. Le code
métier des agents peut désormais être implémenté à l'intérieur de `agents/<nom-agent>/`, en
respectant le périmètre et les permissions de chaque agent (section 5).

## 4. Conventions du projet

- **Langue** : documentation et commits en français ; noms de variables/fonctions en anglais
  (à confirmer une fois la stack fixée).
- **Commits** : messages descriptifs, impératif présent (ex. "Ajoute le scoring des
  prospects"), un commit = un changement cohérent.
- **Branches** : une branche de travail par tâche/fonctionnalité, jamais de commit direct
  sur la branche principale sans revue.
- **Secrets** : jamais de secret, clé ou token en clair dans le dépôt (voir section 5 et
  `config/credentials/README.md`).
- **Structure de dossiers, nommage de fichiers, style de code** : Python (PEP 8, snake_case
  pour modules/fonctions/dossiers de package). Les dossiers `agents/<nom-agent>/` sont en
  snake_case (`creation_site`, `reseaux_sociaux`, `maintenance`, `prospection`) — packages
  Python valides, importables directement (`agents.creation_site`).

## 5. Sécurité et permissions des agents IA

### Ce que tout agent A LE DROIT de faire

- Lire et écrire dans son propre périmètre de données (site du client pour l'agent Création
  de site, contenu réseaux sociaux pour l'agent Réseaux sociaux, fiche prospect pour l'agent
  Prospection, etc.).
- Appeler les API externes nécessaires à sa mission, en utilisant les clés stockées dans
  `config/credentials/` (jamais en dur dans le code).
- Générer du contenu (textes, visuels, code de site) à partir des briefs clients.
- Notifier un humain (l'équipe projet) en cas de décision sensible ou d'anomalie détectée.
- Consulter et mettre à jour `MEMORY.md` pour la partie qui concerne son propre périmètre.

### Ce qu'AUCUN agent N'A LE DROIT de faire

- Exécuter un paiement réel ou modifier un montant facturé sans validation humaine explicite.
- Supprimer des données client (site, fiche prospect, contenu) sans confirmation humaine.
- Contacter un prospect classé **"non favorable"** ou **"non joignable"** après filtrage par
  l'agent Prospection.
- Publier du contenu sur les réseaux sociaux d'un client sans qu'un brief ou une validation
  préalable existe pour ce contenu précis.
- Modifier le code ou la configuration d'un **autre agent** que le sien (cloisonnement
  strict entre agents).
- Stocker, lire ou transmettre la **clé API Claude** — celle-ci est gérée exclusivement en
  dehors de `config/credentials/`, séparément par l'équipe projet.
- Committer un secret, une clé ou un token dans le dépôt Git, sous quelque forme que ce soit
  (y compris dans des logs, des exemples ou des messages de commit).

Ces règles s'appliquent à tout agent IA travaillant sur ce projet, qu'il s'agisse d'un des
4 agents métier de la plateforme ou d'un agent de développement (ex. Claude Code) qui
intervient sur le code du projet lui-même.

## 6. Lancer et tester le projet en local

Scaffolding applicatif créé : package partagé `platform_core/` (config, accès DB, modèles),
app FastAPI + dashboard dans `app/`, migrations Alembic dans `migrations/`. Premier agent
implémenté : Création de site (`agents/creation_site/`, voir son `skills/README.md`). Les 3
autres agents n'ont encore que leur conception (`agents/<nom-agent>/skills/README.md`), pas
de code.

1. Copier `config/credentials/.env.example` vers `config/credentials/.env` et renseigner au
   minimum `DATABASE_URL` (PostgreSQL local ou distant). La clé API Claude n'est **jamais**
   placée ici : elle est fournie à l'exécution par la variable d'environnement standard
   `ANTHROPIC_API_KEY`, définie hors dépôt (nécessaire uniquement pour appeler réellement
   `POST /api/sites/{id}/generate` ; les tests, eux, simulent le client Claude et n'ont besoin
   d'aucune clé).
2. Installer les dépendances (Python ≥ 3.12) : `pip install -e ".[dev]"`
3. Appliquer les migrations : `alembic upgrade head`
4. Lancer l'app : `uvicorn app.main:app --reload`, puis ouvrir `http://localhost:8000`
   (`/healthz` pour vérifier que l'app répond).
5. Lancer les tests : `pytest` (aucun appel réseau réel, y compris vers l'API Claude —
   entièrement simulé).

Déploiement (Fly.io, `fly.toml`) : `fly deploy` après avoir renommé `app` dans `fly.toml`
(nom unique global sur Fly.io) et configuré les secrets (`fly secrets set DATABASE_URL=...`,
etc. — jamais dans `fly.toml` ni dans le dépôt).

## 7. Pour aller plus loin

- `MEMORY.md` : historique des décisions, état d'avancement par agent, problèmes rencontrés.
- `config/credentials/README.md` : liste des clés/API attendues par agent (sans valeurs
  réelles).
- `agents/<nom-agent>/skills/README.md` : skills, frameworks et librairies retenus pour
  chaque agent, avec justification (à créer une fois la stack fixée).
- `docs/pricing-model.md` : modèle de coût unitaire par pack (coût API Claude par action
  d'agent), utilisé pour valider les quotas de la section 1.
