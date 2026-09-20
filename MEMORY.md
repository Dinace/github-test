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

---

## 2026-09-19 — Décisions produit restantes tranchées sur les meilleures pratiques

**Décisions techniques**
- À la demande de l'utilisateur ("le meilleur qui se fait"), Claude tranche les points
  produit encore ouverts en s'appuyant sur les pratiques standards du secteur, documentés
  dans les `skills/README.md` de chaque agent concerné :
- **Création de site** : génération **100% statique (JAMstack)** sur Cloudflare R2 + CDN ;
  dynamique géré sans backend par page (formulaire de contact → endpoint FastAPI, réservation
  → lien WhatsApp `wa.me`). Cycle **brouillon → validation client → publication** (préfixe
  `draft/` puis promotion vers `live/` sur validation), aucune mise à jour ne saute cette
  étape.
- **Prospection** : sources autorisées limitées aux **API officielles en priorité**
  (Google Places API, Meta Graph API) et annuaires publics respectant leur `robots.txt` ;
  **LinkedIn explicitement interdit** (ToS). Scoring par règles pondérées et auditables
  (coordonnées valides, absence de site existant, adéquation sectorielle, signaux
  d'activité récente) déterminant les 4 catégories déjà actées. Premier contact via
  WhatsApp Business, avec le même principe de validation humaine que l'agent Réseaux
  sociaux.
- **Réseaux sociaux** : brief structuré (objectif, ton, éléments obligatoires, visuel,
  date) et workflow à statuts `brouillon → en attente de validation → validé → planifié →
  publié`, seule la transition `validé → publié` déclenche l'appel API réel. Portée MVP
  limitée à Meta + WhatsApp Business (Google Ads différé).
- **Maintenance** : rétention des sauvegardes en rotation grand-père/père/fils alignée sur
  la fréquence par pack (Starter : 3 mois ; Business : ~2 mois hebdo + 3 mois mensuel
  dérivé ; Premium : 30 jours + 12 semaines + 6 mois). Seuils de notification humaine
  précisés (site down 15 min, erreur répétée ≥5×/h, échec de backup immédiat, faille
  haute/critique immédiate). Processus de restauration : l'agent propose, un humain
  confirme explicitement, jamais d'exécution automatique (cohérent avec CLAUDE.md §5).
  Référence `BACKUP_STORAGE_KEY` (obsolète) corrigée vers les variables `CLOUDFLARE_R2_*`.

**État d'avancement par agent**
- Les 4 agents ont désormais une conception produit complète (skills, périmètre,
  permissions, workflows) ; aucun code applicatif n'existe encore.

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Confirmer précisément les conditions d'intégration Airtel Money/Moov Money Gabon
  (documentation API, éligibilité marchande) — nécessite une vérification factuelle, pas
  une décision de conception.
- Valider les quotas chiffrés des packs une fois les coûts API réels connus.
- Scaffolding applicatif réel (pyproject.toml, package partagé FastAPI, migrations Alembic,
  Dockerfile pour Fly.io) non démarré — c'est la seule étape structurante restante avant de
  pouvoir exécuter quoi que ce soit.

---

## 2026-09-19 — Validation des quotas chiffrés via le coût réel de l'API Claude

**Décisions techniques**
- Consultation des tarifs actuels de l'API Claude (skill `claude-api`) : Sonnet 5 à 2 $/10 $
  par million de tokens (input/output), Haiku 4.5 à 1 $/5 $.
- Création de `docs/pricing-model.md` : modèle de coût unitaire par action d'agent (site,
  post, fiche prospect, support d'offre), avec hypothèses de volumétrie de tokens
  explicitement documentées comme estimations de travail à recalibrer avec l'usage réel.
- Résultat : le coût Claude API par client reste **sous 1 $/mois même sur Premium**
  (~0,09 $ Starter, ~0,33 $ Business, ~0,79 $ Premium) — **les quotas définis dans
  CLAUDE.md §1 sont donc validés du point de vue du coût API Claude**, qui n'est pas le
  facteur limitant de la viabilité des packs.
- Choix de modèle par défaut documenté dans `docs/pricing-model.md` : Haiku 4.5 pour les
  tâches courtes/répétitives (posts, fiches prospect), Sonnet 5 pour les tâches demandant
  plus de qualité rédactionnelle (contenu de site, supports d'offre) — choix de coût,
  réévaluable si la qualité observée en pratique est insuffisante.
- Les vrais leviers de coût identifiés comme non encore chiffrés : tarification WhatsApp
  Business API par conversation au Gabon, coût Google Places API selon le volume de l'agent
  Prospection, coût infrastructure à l'échelle, temps humain (support/onboarding).
- `CLAUDE.md` §1 mis à jour pour refléter cette validation partielle des quotas.

**État d'avancement par agent**
- Inchangé (aucun code applicatif).

**Problèmes rencontrés / solutions**
- Aucun.

**Questions ouvertes**
- Tarification WhatsApp Business API par conversation au Gabon (à obtenir avant de fixer le
  prix final des packs).
- Coût Google Places API selon le volume réel de requêtes de l'agent Prospection.
- Prix d'abonnement final par pack en FCFA — décision commerciale, pas technique.
- Confirmer précisément les conditions d'intégration Airtel Money/Moov Money Gabon.
- Recalibrer les estimations de tokens de `docs/pricing-model.md` avec des mesures réelles
  (`response.usage`) une fois l'app en production.
- Scaffolding applicatif réel (pyproject.toml, package partagé FastAPI, migrations Alembic,
  Dockerfile pour Fly.io) non démarré — c'est la seule étape structurante restante avant de
  pouvoir exécuter quoi que ce soit.

---

## 2026-09-19 — Recherche de marché sur les points commerciaux restants

**Décisions techniques**
- Recherche web menée sur les 4 inconnues commerciales listées ci-dessus ; résultats ajoutés
  dans `docs/pricing-model.md` (section "Données de marché").
- **WhatsApp Business API** : correction importante — la tarification "à la conversation"
  est obsolète depuis juillet 2025 ; le modèle actuel facture **au message envoyé**
  (catégories marketing/utility/authentication), tarif dépendant du pays du destinataire.
  Aucun tarif Gabon publié publiquement par Meta ; marge BSP typique 0,003–0,010 $/message
  en plus. Un devis direct auprès d'un BSP couvrant le Gabon reste nécessaire.
- **Google Places API** : Place Details ≈ 17–40 $/1000 requêtes selon les champs demandés ;
  impact estimé sur le pack Premium (60 fiches/mois) : ~1,20–2,40 $/mois/client — plus
  significatif que le coût Claude API mais reste modeste.
- **Airtel Money Gabon** : donnée concrète trouvée — intégration marchande facturée
  **350 000 à 600 000 FCFA en coût ponctuel** (délai 3–5 jours, majoritairement KYC), puis
  **~2% de commission sur le volume collecté**. Premier chiffre concret à intégrer au
  business plan.
- **Moov Money Gabon** : produit marchand confirmé existant, mais aucune grille de frais
  publique trouvée — contact direct nécessaire.
- Aucune modification des décisions de conception (workflow de validation avant tout envoi
  WhatsApp inchangé, cf. `skills/README.md` des agents Réseaux sociaux et Prospection) —
  seul le modèle de facturation sous-jacent est corrigé, pas le produit.

**État d'avancement par agent**
- Inchangé (aucun code applicatif).

**Problèmes rencontrés / solutions**
- Recherche web ne fournit pas de tarif Gabon exact pour WhatsApp (dépend du destinataire,
  pas publié par pays hors grands marchés) ni de grille de frais Moov Money — ces deux
  points nécessitent un contact/devis direct, pas seulement de la recherche.

**Questions ouvertes**
- Devis direct BSP pour le tarif WhatsApp Business par message, destinataires au Gabon.
- Contact direct Moov Money Gabon pour la grille de commission marchande ; reconfirmer
  celle d'Orange Money.
- Prix d'abonnement final par pack en FCFA — décision commerciale, pas technique.
- Budgéter le coût d'intégration paiement (~350–600k FCFA pour Airtel Money, montant
  probablement similaire pour Moov Money) dans le plan de lancement.
- Recalibrer les estimations de tokens de `docs/pricing-model.md` avec des mesures réelles
  une fois l'app en production.

---

## 2026-09-19 — Cadre de prix + scaffolding applicatif

**Décisions techniques**
- **Cadre de réflexion prix** ajouté à `docs/pricing-model.md` : plancher de coût variable
  chiffré par pack (600–6 700 FCFA/mois selon le pack), distingué explicitement de la
  disposition à payer réelle des clients gabonais (inconnue, nécessite une validation
  terrain — entretiens clients, test de prix, pas une recherche web). Une fourchette
  hypothèse de travail est proposée (Starter 8-15k, Business 20-35k, Premium 40-70k
  FCFA/mois) mais explicitement marquée comme non validée.
- **Scaffolding applicatif créé et testé** : package partagé `platform_core/` (config via
  pydantic-settings lisant `config/credentials/.env`, accès DB SQLAlchemy, modèles `Client`
  et `Subscription` — ce dernier avec `country`/`currency`/`payment_provider` en champs
  paramétrables, pas codés en dur, conformément au principe multi-pays de CLAUDE.md §1) ;
  app FastAPI + dashboard Jinja2/HTMX/Alpine/Tailwind (CDN, à remplacer par un build compilé
  avant prod) dans `app/` ; migrations Alembic dans `migrations/` ; `Dockerfile` + `fly.toml`
  pour le déploiement Fly.io (`config/` jamais copié dans l'image — secrets via Fly secrets
  à l'exécution).
- Validation réelle effectuée (pas seulement écrite) : installation des dépendances,
  `pytest` (2 tests passent : `/healthz`, page d'accueil du dashboard), et
  `alembic revision --autogenerate` testé avec succès contre une base SQLite jetable
  (détecte bien les tables `clients`/`subscriptions`) — fichiers de test supprimés après
  vérification, non commités.
- Point d'attention documenté dans `CLAUDE.md` §4 : les dossiers `agents/<nom-agent>/` sont
  en kebab-case, invalide comme nom de package Python — pas bloquant tant qu'ils ne
  contiennent que de la documentation, mais à trancher avant d'y ajouter du code agent
  (import par chemin de fichier vs renommage en snake_case).
- `CLAUDE.md` §6 mis à jour avec les vraies instructions de lancement local et de
  déploiement Fly.io.

**État d'avancement par agent**
- Plateforme : scaffolding applicatif exécutable pour la première fois (health check,
  dashboard placeholder, modèle de données de base). Aucun code métier des 4 agents encore
  implémenté — reste à faire.

**Problèmes rencontrés / solutions**
- Aucun ; tout a fonctionné du premier coup (venv Python 3.12, dépendances, tests, Alembic).

**Questions ouvertes**
- Implémenter le code métier des agents (Claude Agent SDK, prompts, outils) — non démarré,
  dépend de la résolution du point de nommage kebab-case/snake_case ci-dessus.
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé,
  voir entrées précédentes.
- Recalibrer les estimations de coût une fois l'app en production.

---

## 2026-09-20 — Premier agent implémenté : Création de site

**Décisions techniques**
- **Renommage** `agents/creation-site/` → `agents/creation_site/` et
  `agents/reseaux-sociaux/` → `agents/reseaux_sociaux/` (snake_case, packages Python
  valides) — résout le point d'attention posé dans l'entrée précédente. Toutes les
  références dans `CLAUDE.md` mises à jour ; les entrées passées de ce journal gardent
  volontairement l'ancien nom (historique, jamais réécrit).
- **Correction d'architecture** : CLAUDE.md §3 indiquait "Claude Agent SDK" comme choix
  unique d'orchestration. En implémentant l'agent Création de site, ce choix s'est révélé
  inadapté pour cette tâche précise : générer du contenu à partir d'un brief structuré est
  un appel unique (brief -> JSON), pas une exploration agentique ouverte à plusieurs étapes
  — le Agent SDK (harnais complet avec accès Bash/fichiers) aurait donné à cet agent un
  accès qu'il n'a aucune raison d'avoir, contraire au cloisonnement strict (CLAUDE.md §5).
  Choix retenu : **appel direct à l'API Claude** (SDK `anthropic`, modèle `claude-sonnet-5`
  déjà validé dans `docs/pricing-model.md`). `CLAUDE.md` §3 reformulé pour ne plus imposer
  un choix d'orchestration unique aux 4 agents : à trancher agent par agent selon la forme
  réelle de sa tâche.
- **Modèle de données ajouté** (`platform_core/models.py`) : table `Site` (client_id,
  secteur, `brief`/`content` en JSON — JSONB sur PostgreSQL via `.with_variant()`, JSON
  générique en repli sur les autres dialectes pour rester testable en SQLite —, statut
  `draft`/`published`, `published_at`). Migration Alembic initiale générée et testée
  (`alembic upgrade head` appliqué avec succès sur une base SQLite jetable) ; un bug connu
  d'Alembic (import `Text` manquant avec `.with_variant()`) a été corrigé manuellement dans
  le fichier de migration généré.
- **Code de l'agent** (`agents/creation_site/`) : `brief.py` (SiteBrief, catalogue Sector),
  `content.py` (génération de contenu via l'API Claude, validation stricte du JSON retourné
  avec erreur explicite si non conforme), `render.py` (rendu Jinja2 avec repli automatique
  vers le template générique), `publish.py` (écriture du brouillon — **en local pour
  l'instant**, l'upload réel vers Cloudflare R2 reste à faire, nécessite des credentials
  réels pour être testé), `agent.py` (orchestration brief -> contenu -> rendu -> brouillon).
  Deux templates Jinja2 construits (`restaurant`, `generique`) sur les 10 du catalogue ; les
  7 autres retombent sur le générique en attendant leur design.
  Exposé via `app/routers/sites.py` : create / generate / preview / publish.
- **Tests** (9 au total, tous passent) : génération de contenu avec client Claude simulé
  (aucun appel réseau réel, donc aucun coût ni besoin de clé API pour lancer la suite),
  rendu Jinja2 (dont le repli vers le générique), et le flux complet de l'API avec une base
  SQLite jetable et génération de contenu simulée.

**État d'avancement par agent**
- Création de site : premier agent avec du vrai code, testé de bout en bout (hors upload R2
  réel et authentification, notés comme restants). Les 3 autres agents : conception
  seulement, aucun code.

**Problèmes rencontrés / solutions**
- `JSONB` (PostgreSQL) non compilable par SQLite lors des tests → résolu avec
  `JSON().with_variant(JSONB(), "postgresql")` (JSONB en prod, JSON générique en test).
- Migration Alembic générée avec un import manquant (`Text`) → corrigé manuellement.
- Un test comparait une chaîne contenant une apostrophe au HTML rendu sans tenir compte de
  l'échappement automatique de Jinja2 (comportement correct, à ne jamais désactiver) →
  chaîne de test corrigée plutôt que le code.

**Questions ouvertes**
- Upload réel vers Cloudflare R2 (`draft/`/`live/`) — nécessite des credentials réels.
- Authentification/autorisation des endpoints `/api/sites/*` — inexistante à ce stade.
- Construire les 7 templates de secteur restants.
- Implémenter les 3 autres agents (Réseaux sociaux, Maintenance, Prospection) — trancher
  pour chacun API directe vs Agent SDK vs Tool Runner selon la forme de leur tâche réelle
  (ex. la Prospection, qui doit chercher/naviguer, pourrait justifier un usage d'outils plus
  proche de l'agentique que la Création de site).
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé.

---

## 2026-09-20 — Agent Création de site complété (templates, R2, authentification)

**Décisions techniques**
- **10/10 templates de secteur construits** (`agents/creation_site/templates/sectors/`) :
  les 7 restants (boutique, beauté & bien-être, artisanat, services professionnels, santé,
  hôtellerie & tourisme, éducation & formation, événementiel) suivent le même mécanisme que
  `restaurant`/`generique` — héritage de `base.html.jinja` avec libellé de section adapté.
  Le template `sante` porte un commentaire Jinja (non visible visiteur) rappelant la
  contrainte "aucun contenu médical sans validation professionnelle" déjà appliquée au
  niveau du prompt de génération — filet de sécurité en plus, pas une nouvelle règle.
- **Upload réel vers Cloudflare R2** (`agents/creation_site/storage.py`, via `boto3`,
  compatible S3) : `upload_draft` écrit sous `draft/<site_id>/`, `promote_to_live` copie
  vers `live/<site_id>/` à la validation. Le fichier `publish.py` (écriture locale,
  placeholder) est supprimé, remplacé par ce module. Client S3 injectable pour les tests —
  aucune connectivité réelle à R2 vérifiée (pas de credentials disponibles), seule la
  logique (clés, préfixes, copie) est testée avec un client simulé.
- **Authentification par clé API** (`platform_core/auth.py`, `app/auth.py`) : clé aléatoire
  haute entropie hachée en SHA-256 (choix justifié : correct pour un secret déjà
  haute-entropie, contrairement à un mot de passe humain qui demanderait bcrypt/argon2).
  Nouveau champ `Client.api_key_hash` (migration Alembic dédiée, séparée de la migration
  initiale — jamais réécrire une migration existante). Nouvel endpoint `POST /api/clients`
  (crée un client, retourne la clé API une seule fois). Tous les endpoints
  `app/routers/sites.py` exigent désormais `Authorization: Bearer <clé>` et vérifient que le
  site appartient au client authentifié (403 sinon) — corrige au passage une faille de
  cloisonnement : l'ancien `POST /api/sites` acceptait un `client_id` arbitraire en
  paramètre, permettant de créer un site pour n'importe quel client sans vérification.
  Portée explicitement limitée à une authentification machine-à-machine par clé API ; le
  login humain avec session pour le dashboard reste à concevoir séparément.
- 24 tests au total (contre 9 avant cette session), tous passent, toujours aucun appel
  réseau réel (Claude et R2 tous deux simulés dans les tests).

**État d'avancement par agent**
- Création de site : fonctionnellement complet pour le MVP (10 templates, génération,
  stockage R2, cycle brouillon/validation/publication, authentification/cloisonnement par
  client). Restent : vérification de connectivité R2 réelle (credentials manquants), login
  humain pour le dashboard. Les 3 autres agents : conception seulement, aucun code.

**Problèmes rencontrés / solutions**
- `alembic revision --autogenerate` contre SQLite a généré du bruit (faux changements de
  type `NUMERIC()` → `UUID()` sur des colonnes inchangées, artefact de la faible typologie
  de SQLite) en plus du vrai changement (`api_key_hash`) → migration nettoyée manuellement
  pour ne garder que les opérations réelles avant de la committer.
- Un test simulant `Environment.get_template` de Jinja2 a échoué car Jinja2 appelle cette
  méthode avec des arguments positionnels supplémentaires en interne (résolution de
  `{% extends %}`) → wrapper de test corrigé pour accepter `*args, **kwargs`.

**Questions ouvertes**
- Vérifier la connectivité réelle à R2 une fois `config/credentials/.env` renseigné.
- Concevoir le login humain du dashboard (au-delà de la clé API machine-à-machine).
- Implémenter les 3 autres agents (Réseaux sociaux, Maintenance, Prospection).
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé.

---

## 2026-09-20 — Agent Réseaux sociaux implémenté + deux bugs de packaging corrigés

**Décisions techniques**
- **Agent Réseaux sociaux** (`agents/reseaux_sociaux/`) implémenté selon la conception déjà
  actée : `brief.py` (`PostBrief`/`PostObjective`), `content.py` (génération du texte de
  publication via API Claude directe — même correction que Création de site, pas le Agent
  SDK), `meta.py` (publication réelle sur Meta Graph API via `httpx`, `MetaPublishError`
  explicite). **WhatsApp volontairement non implémenté** : ce n'est pas une "publication"
  au sens réseau social (canal de messagerie à opt-in avec templates approuvés, flux
  différent) — décision de ne pas le faire à moitié plutôt que de fabriquer un faux
  fonctionnement.
- Nouveau modèle `Post` (statuts stricts : `draft` → `pending_validation` → `validated` →
  `scheduled` → `published`, aucun raccourci, conforme au workflow déjà documenté) et
  nouveaux champs `Client.brand_voice`/`meta_page_id`/`meta_page_access_token` (migration
  Alembic dédiée, nettoyée du même bruit SQLite que les migrations précédentes).
- Endpoints `app/routers/posts.py` (create/generate/request-changes/validate/schedule/
  publish), authentifiés et cloisonnés par client comme `sites.py` ; `publish` renvoie 412
  si le client n'a pas connecté sa Page Meta plutôt que d'échouer silencieusement.
- **Deux bugs de packaging découverts et corrigés en testant une vraie installation non-
  éditable** (`pip install .` depuis un répertoire externe, pour simuler ce qui se passe
  réellement dans l'image Docker construite avec la même commande) :
  1. `agents*` manquait de `[tool.setuptools.packages.find]` — le package n'était jamais
     enregistré par `pip install .` ; ça fonctionnait seulement en dev parce que le
     répertoire courant se retrouve sur `sys.path` dans ce cas précis (fragile, invisible
     tant qu'on ne teste que via `pytest`/`pip install -e .` depuis la racine du repo).
  2. setuptools n'inclut par défaut que les fichiers `.py` d'un package : les templates
     Jinja2 (`agents/creation_site/templates/*.jinja`) et les fichiers de `app/templates`/
     `app/static` étaient absents d'une installation non-éditable, sans erreur au moment de
     l'install — seulement au runtime. Pire : `app/static` ne contenant que `.gitkeep`, le
     dossier n'existait pas du tout après installation, et `StaticFiles(directory=...)`
     plante au démarrage si ce dossier est absent (`app.main` n'aurait jamais démarré dans
     l'image Docker). Corrigé avec `[tool.setuptools.package-data]`.
  3. `Dockerfile` ne copiait jamais `agents/`, et `.dockerignore` l'excluait explicitement
     en plus — l'image de production n'aurait jamais contenu le code des agents. Corrigé
     (`.dockerignore` exclut maintenant seulement `agents/*/skills/`, la documentation, pas
     le code).
  Validé concrètement : install non-éditable dans un venv propre + import + `TestClient`
  depuis `/tmp` (le daemon Docker n'est pas disponible dans cet environnement pour un vrai
  `docker build`, ce test est l'équivalent le plus proche possible).
- 35 tests au total (contre 24 avant cette session), tous passent, toujours aucun appel
  réseau réel (Claude, R2 et Meta tous simulés dans les tests).

**État d'avancement par agent**
- Réseaux sociaux : fonctionnellement complet pour le MVP côté Meta (génération, workflow
  de validation à 5 statuts, publication réelle). WhatsApp explicitement hors périmètre pour
  l'instant. Restent : flux OAuth de connexion Meta, vraie planification automatique
  (actuellement `/publish` est un appel manuel, rien ne le déclenche à `scheduled_at`),
  génération de visuels (Pillow, non commencée).
- Maintenance et Prospection : conception seulement, aucun code.

**Problèmes rencontrés / solutions**
- Voir les 3 bugs de packaging ci-dessus, découverts uniquement parce qu'un test
  d'installation non-éditable depuis un répertoire externe a été fait spontanément (aucun
  des deux ne remontait dans `pytest` classique, qui masque le problème par construction).

**Questions ouvertes**
- Construire une vraie tâche planifiée (Celery beat/APScheduler) qui déclenche `/publish`
  à `scheduled_at`, au lieu d'un appel manuel.
- Flux OAuth de connexion Meta (Facebook Login, sélection de Page, refresh de token).
- Génération de visuels (Pillow) — pas commencée.
- Chiffrement au repos de `Client.meta_page_access_token`.
- Implémenter Maintenance et Prospection.
- Vérifier un vrai `docker build`/`fly deploy` dès qu'un environnement avec Docker actif ou
  un compte Fly.io est disponible — validé seulement par équivalent (install non-éditable)
  ici.
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé.

---

## 2026-09-20 — Agent Maintenance implémenté (backups, monitoring, sécurité, restauration)

**Décisions techniques**
- **Rotation grand-père/père/fils implémentée réellement** (`agents/maintenance/backup.py`,
  fonction pure `keys_to_retain`), pas juste documentée : pour Business/Premium, dérive un
  backup hebdomadaire ou mensuel "représentatif" (le plus récent de chaque période ISO) au-
  delà de la fenêtre la plus fine, fidèle au tableau déjà acté dans le skills/README.md.
  Testée avec des historiques synthétiques de plusieurs mois pour les 3 packs.
- **Sentry** : l'app est réellement instrumentée (`sentry_sdk.init` dans `app/main.py`, pas
  seulement documentée) — les vraies erreurs de la plateforme remonteront dans Sentry une
  fois `SENTRY_DSN` renseigné. Décision architecturale : le seuil "≥5 fois en 1h" n'est
  **pas réimplémenté** en Python, il vit dans une règle d'alerte configurée côté Sentry lui-
  même (plus robuste que de le refaire nous-mêmes) ; un endpoint webhook reçoit l'alerte et
  crée une `Notification`.
- **Processus de restauration** implémenté avec un vrai garde-fou côté code (pas seulement
  côté API) : `execute_restore` lève `RestoreNotConfirmedError` si le statut n'est pas
  `confirmed`, quel que soit l'appelant — cohérent avec l'interdiction CLAUDE.md §5.
- **Nouveaux modèles** : `Notification` (catégorie/sévérité/statut, rattachable à un client/
  site en contexte), `Backup`, `RestoreRequest`. Migration Alembic dédiée (bruit SQLite
  habituel nettoyé avant commit).
- **Décision de trust boundary** : contrairement aux sites/posts (par client, API key
  client), les opérations de Maintenance (backup, restauration, notifications) sont
  **platform-wide** (PostgreSQL est une base partagée entre tous les clients, CLAUDE.md §3 —
  un pg_dump couvre toute la plateforme, pas un client isolé) et relèvent du staff, pas du
  client. Comme aucun système d'auth staff n'existe, un jeton partagé unique
  (`OPS_API_TOKEN`, `app/auth.py::require_ops_token`) sert de verrou minimal — **stopgap
  explicite**, documenté comme tel à 3 endroits (config, skills/README.md, CLAUDE.md) pour
  qu'il ne soit pas confondu avec un vrai système d'auth.
- **Faille assumée et documentée, pas cachée** : le webhook `POST /api/maintenance/webhooks/
  sentry` n'a aucune vérification de signature — n'importe qui peut aujourd'hui y injecter
  une fausse alerte. Choix délibéré de livrer la fonctionnalité avec cette limite clairement
  marquée plutôt que de bloquer tout l'agent dessus, mais **à corriger avant tout déploiement
  réel**.
- Honnêteté sur une incertitude : le schéma JSON exact de `pip-audit --format=json` (en
  particulier la présence d'un champ de sévérité) n'a pas été vérifié contre une exécution
  réelle ni une doc à jour dans cette session — noté explicitement dans
  `agents/maintenance/security_scan.py` et son skills/README.md plutôt que présenté comme
  certain.
- Réutilise le client R2 existant (`agents.creation_site.storage.get_r2_client`) pour les
  sauvegardes plutôt que d'en dupliquer un — un seul bucket, mêmes credentials.
- 57 tests au total (contre 35 avant cette session), tous passent. Packaging non-éditable
  revérifié après ajout du nouveau module (`agents.maintenance`) : toujours correct, aucun
  bug de packaging supplémentaire introduit.

**État d'avancement par agent**
- Maintenance : logique métier complète et testée (rétention, seuils, restauration,
  sécurité), exposée via API avec un stopgap d'auth staff. Restent : vraie tâche planifiée
  (rien ne déclenche automatiquement backup/scan/monitoring pour l'instant, appels manuels),
  vérification de signature du webhook Sentry, vraie auth staff, connectivité réelle jamais
  vérifiée (Postgres/R2/UptimeRobot/Sentry tous simulés dans les tests).
- Prospection : conception seulement, aucun code — dernier agent restant.

**Problèmes rencontrés / solutions**
- Aucun bug bloquant cette fois (contrairement à la session précédente) — la vérification
  systématique du packaging non-éditable après chaque nouvel agent a payé : rien à corriger.

**Questions ouvertes**
- Construire les vraies tâches planifiées (backup, scan sécurité, vérification uptime par
  site) — actuellement des endpoints à appel manuel.
- Vérifier la signature des webhooks Sentry avant tout déploiement réel.
- Concevoir un vrai système d'auth staff (remplacer `OPS_API_TOKEN`).
- Ajouter un `uptime_monitor_id` par `Site` pour relier vérification et site concerné.
- Scan de sécurité des sites clients eux-mêmes (en-têtes HTTP), pas seulement des
  dépendances Python de la plateforme.
- Vérifier la connectivité réelle (pg_dump/psql, R2, UptimeRobot, Sentry) dès que
  l'environnement le permet.
- Implémenter Prospection — dernier agent de la plateforme.
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé.

---

## 2026-09-20 — Agent Prospection implémenté : les 4 agents de la plateforme ont du code

**Décisions techniques**
- **Garde-fou de conformité codé en dur** (`agents/prospection/compliance.py`,
  `assert_source_allowed`) : la règle "LinkedIn interdit, sans exception" est désormais
  vérifiée EN CODE avant toute requête de collecte, pas seulement documentée — décision
  volontairement plus stricte que pour les autres agents, vu l'impact en cas d'erreur
  (risque juridique/ToS réel, pas seulement une mauvaise fiche prospect).
- **Scoring pondéré réellement implémenté** (`agents/prospection/scoring.py`,
  `score_prospect`) : fonction pure, poids et seuils en paramètres (`ScoringWeights`), pas
  codés en dur — fidèle à l'exigence d'auditabilité déjà actée. Coordonnées invalides →
  `non_joignable` immédiat sans calcul de score, comme documenté.
- **Google Places API (New)** comme source principale (`sources/google_places.py`) — clé
  dédiée `GOOGLE_PLACES_API_KEY` ajoutée, distincte de `GOOGLE_BUSINESS_PROFILE_TOKEN` (qui
  gère la fiche du client lui-même, pas la recherche d'autres établissements). Note
  d'honnêteté : schéma de réponse non vérifié contre un appel réel (pas de clé disponible).
- **Nouveau modèle `Prospect`** avec un double workflow : `category` (calculé une fois à la
  création, jamais recalculé — empêche qu'un prospect "non favorable" ne redevienne
  contactable sans nouvelle collecte explicite) et `contact_status` (none → pending_
  validation → validated → sent, même logique de validation humaine que Réseaux sociaux).
  Ajout de `Client.whatsapp_phone_number_id`/`whatsapp_access_token` (même pattern que
  `meta_page_id`/`meta_page_access_token`).
- **Blocage 403 codé en dur, pas seulement documenté** : `POST /api/prospects/{id}/
  propose-contact` refuse toute génération de message si `category` est `non_favorable` ou
  `non_joignable` ; `send-contact` re-vérifie la même règle en défense en profondeur avant
  l'envoi réel — cohérent avec l'interdiction stricte de CLAUDE.md §5, appliquée à deux
  endroits du code, pas comptée sur une seule vérification.
- Portée volontairement limitée par rapport au skills/README.md d'origine : Playwright,
  Meta Graph API pour la recherche (par opposition à la publication, déjà faite côté Réseaux
  sociaux), et python-pptx ne sont **pas implémentés** — seuls Google Places, BeautifulSoup
  (annuaires) et ReportLab (PDF) le sont. Choix assumé : livrer un chemin complet et
  fonctionnel plutôt que plusieurs chemins à moitié faits.
- 85 tests au total (contre 57 avant cette session), tous passent. Packaging non-éditable
  revérifié une dernière fois : toujours correct.

**État d'avancement par agent**
- Prospection : logique métier complète et testée pour le chemin Google Places (scoring,
  structuration, message de contact, envoi WhatsApp, offre PDF). Restent : Playwright, Meta
  Graph API pour la recherche, python-pptx, flux de connexion WhatsApp, détection réelle de
  site "obsolète", connectivité réelle jamais vérifiée.
- **Les 4 agents de la plateforme ont désormais du code** (Création de site, Réseaux
  sociaux, Maintenance, Prospection) — la conception initiale posée en tout début de projet
  est maintenant entièrement implémentée en MVP, avec pour chaque agent les limites
  restantes explicitement documentées plutôt que cachées.

**Problèmes rencontrés / solutions**
- Un test de scoring avait une hypothèse incorrecte sur les poids par défaut (un score de 3
  atteignait déjà le seuil "favorable", pas "à qualifier" comme supposé) → test corrigé pour
  isoler proprement la propriété visée (seuil relevé explicitement) plutôt que de changer le
  code de scoring, qui était correct.

**Questions ouvertes**
- Playwright, Meta Graph API pour la recherche de prospects, python-pptx — non implémentés.
- Flux de connexion WhatsApp Business (comme Meta) — credentials manuels en attendant.
- Détection réelle de site "obsolète" (nécessiterait de visiter le site).
- Vérifier la connectivité réelle (Google Places, WhatsApp Cloud API) dès que possible.
- Toutes les questions ouvertes des agents précédents restent valables (tâches planifiées
  réelles, vraie auth staff, vérification de signature Sentry, flux OAuth Meta, génération
  de visuels Pillow, login humain du dashboard, etc.) — voir les entrées précédentes.
- Devis direct BSP (WhatsApp), contact Moov Money Gabon, prix d'abonnement final — inchangé.

---

## 2026-09-20 — Agent Planning ajouté (suivi transverse + RDV, outil interne hors packs)

**Décisions techniques**
- **Cadrage clarifié avec l'utilisateur avant tout code** (2 questions posées) : Planning
  doit suivre (a) l'activité de chaque client à travers les 4 agents et (b) le pipeline de
  chaque prospect dans le temps ; les RDV sont **staff <-> client PME** (onboarding, suivi
  commercial), pas un module public de prise de RDV pour les clients finaux du PME.
- **Décision de framing actée** : Planning n'est **pas un 5e agent vendu dans les packs**
  (CLAUDE.md §1) — c'est un outil interne à l'équipe qui opère la plateforme, avec une vue
  limitée exposée au client (son propre résumé, ses propres RDV). Documenté comme tel dans
  CLAUDE.md §2 (nouvelle sous-section dédiée, séparée de la table des 4 agents) pour ne pas
  fausser la table des packs.
- **Nouveau concept transverse** : `platform_core.models.ActivityEvent` + `platform_core.
  activity.log_event` — un journal d'événements **partagé entre agents**, qui vit dans le
  package partagé (pas dans un agent précis) précisément parce que plusieurs agents y
  écrivent. Ce n'est pas une exception au cloisonnement (CLAUDE.md §5) : chaque agent ne
  journalise que ses propres événements, jamais les données propres d'un autre agent.
  Seul Prospection émet des événements pour l'instant (`created`, `contact_proposed`,
  `contact_validated`, `contact_sent`) — les 3 autres agents ne sont pas encore instrumentés.
- **Nouveau modèle `Appointment`** (staff <-> client), cycle de vie complet (proposed →
  confirmed/cancelled → completed), avec un `staff_contact` en texte libre faute de vrai
  système de comptes staff (même limite que `OPS_API_TOKEN`).
- **Deux routeurs séparés** (`app/routers/planning.py`) avec deux niveaux d'accès distincts
  dans le même fichier : `staff_router` (OPS_API_TOKEN, réutilisé de Maintenance) pour voir
  n'importe quel client/prospect et gérer tous les RDV ; `client_router` (clé API du client)
  pour son propre résumé et ses propres RDV, avec vérification de propriété comme les
  autres agents.
- **Synthèse en langage naturel** (`digest.py`) via API Claude directe (même correction
  que les 4 autres agents) — transforme les compteurs structurés du résumé en 2-3 phrases
  pour l'équipe.
- **Bug SQLAlchemy réel découvert et corrigé** : `Site.content.isnot(None)` ne filtrait
  rien, car SQLAlchemy stocke par défaut un `None` Python dans une colonne `JSON` comme un
  littéral JSON `"null"`, pas un vrai `NULL` SQL. Corrigé à la racine
  (`JSON(none_as_null=True)` sur le type `_JSONB` partagé), ce qui corrige aussi ce
  comportement pour `Post.content`/`Prospect.contact_message` qui utilisent le même type —
  un bug qui existait silencieusement depuis la création de ces colonnes, révélé seulement
  parce que Planning est le premier agent à filtrer en SQL sur la nullité d'une colonne JSON
  (les autres agents ne faisaient cette vérification qu'en Python, après récupération d'un
  objet unique, ce qui ne révèle pas le problème).
- 100 tests au total (contre 85 avant cette session), tous passent. Packaging non-éditable
  revérifié une dernière fois : toujours correct.

**État d'avancement par agent**
- Planning : logique métier complète et testée (résumé transverse, historique de pipeline,
  cycle de vie des RDV, synthèse Claude). Restent : instrumenter les 3 autres agents pour
  qu'ils émettent aussi des événements, brancher les rappels WhatsApp sur les RDV, vraie
  synchronisation calendrier externe, vrai système de comptes staff.
- Les 4 agents produit + l'outil interne Planning ont désormais tous du code.

**Problèmes rencontrés / solutions**
- Voir le bug SQLAlchemy `none_as_null` ci-dessus — découvert par un test qui vérifiait
  explicitement le comportement d'agrégation (créer un site avec `content=None` et un autre
  avec du contenu, puis vérifier que seul le second est compté), pas une inspection de code.

**Questions ouvertes**
- Instrumenter Création de site, Réseaux sociaux et Maintenance pour qu'ils émettent aussi
  des événements vers `ActivityEvent` (seul Prospection le fait pour l'instant).
- Brancher les rappels de RDV automatiques (réutiliser `agents.prospection.whatsapp`).
- Synchronisation avec un vrai calendrier externe (Google Calendar) côté staff.
- Vrai système de comptes staff (remplacer le `staff_contact` en texte libre et
  `OPS_API_TOKEN`, cohérent avec la question déjà ouverte pour Maintenance).
- Toutes les questions ouvertes des agents précédents restent valables — voir les entrées
  précédentes (tâches planifiées réelles, flux OAuth Meta, login humain du dashboard, devis
  BSP/Moov Money, prix d'abonnement final, etc.).

## 2026-09-20 — "Réalise le non fait" : deux failles de sécurité corrigées

**Contexte** : demande explicite de traiter les éléments accumulés en "points ouverts" dans
les 5 `skills/README.md`. Périmètre trop large pour tout traiter d'un coup ; ce lot se
concentre sur les deux corrections de sécurité les plus simples et les plus importantes,
annoncées à l'utilisateur avant de commencer.

**Chiffrement au repos des tokens clients**
- `platform_core/encryption.py` : `encrypt_token`/`decrypt_token` (Fernet, `cryptography`).
  Dégradation explicite en passe-plat (retourne la valeur telle quelle) si
  `TOKEN_ENCRYPTION_KEY` n'est pas configurée — pour ne jamais casser le développement local
  ni la suite de tests existante, mais à combler impérativement avant une vraie mise en
  production (documenté dans `config/credentials/README.md`).
- `platform_core/models.py` : nouveau `EncryptedString` (`TypeDecorator` SQLAlchemy autour
  de `String`), appliqué à `Client.meta_page_access_token` et `Client.whatsapp_access_token`
  (longueur doublée, 500→1000, pour absorber le surcoût du ciphertext Fernet). Transparent
  pour tout le code applicatif existant (Réseaux sociaux, Prospection) : il continue de
  lire/écrire du texte en clair, seule la colonne SQL change.
- Migration `159f376bd70b` : `alter_column` sur les deux colonnes, dans un
  `batch_alter_table` (nécessaire pour que ça fonctionne aussi sur SQLite en test, qui ne
  supporte pas `ALTER COLUMN ... TYPE` directement — sans effet sur PostgreSQL). Vérifiée
  upgrade et downgrade sur une base SQLite fraîche.
- Testé : passe-plat sans clé, aller-retour chiffrement/déchiffrement avec une vraie clé
  Fernet générée, échec de déchiffrement avec la mauvaise clé (`TokenDecryptionError`), et
  vérification que la valeur brute stockée en base (lue en contournant l'ORM) n'est jamais
  le texte en clair.

**Signature HMAC du webhook Sentry**
- `app/routers/maintenance.py::_sentry_signature_is_valid` : vérifie l'en-tête
  `Sentry-Hook-Signature` par HMAC-SHA256 du corps brut de la requête (`hmac.compare_digest`,
  pas de comparaison naïve pour éviter une attaque par timing), avec le secret
  `SENTRY_WEBHOOK_SECRET`. Corps lu via `await request.body()` avant tout parsing JSON (le
  HMAC porte sur les octets exacts envoyés par Sentry, pas sur une reconstruction).
- Même principe de dégradation explicite : si `SENTRY_WEBHOOK_SECRET` n'est pas configuré,
  la vérification est ignorée (comportement précédent, non sécurisé mais documenté) plutôt
  que de rejeter tout webhook tant que le secret n'est pas en place.
- Testé : webhook accepté avec une signature valide, rejeté (401) avec une signature
  invalide ou absente quand le secret est configuré, comportement inchangé (accepté) sans
  secret configuré — aucune régression sur le test existant.

**Divers**
- Ajout de `cryptography` (chiffrement) et `apscheduler` (à venir : tâches planifiées) aux
  dépendances du projet.
- Environnement de dev reconstruit dans un vrai virtualenv Python 3.12 (`.venv/`, gitignoré)
  — le conteneur de cette session n'avait pas d'environnement préexistant malgré les commits
  précédents ; `pip install -e ".[dev]"` échouait avec `python3` (3.11) car
  `requires-python = ">=3.12"`.
- 107 tests au total (contre 100 avant ce lot), tous passent. Packaging non-éditable
  revérifié dans un nouveau `/tmp/test-install-venv` : imports et démarrage de l'app OK.

**Questions ouvertes restantes (non traitées dans ce lot)**
- Infrastructure de planification (APScheduler) pour débloquer : auto-publication des posts
  programmés (Réseaux sociaux), tâches récurrentes backup/rétention/scan sécurité/uptime
  (Maintenance), rappels de RDV (Planning). Dépendance déjà ajoutée, câblage pas encore fait.
- Instrumentation `ActivityEvent` manquante pour Création de site et Réseaux sociaux (seul
  Prospection émet des événements pour l'instant).
- Toutes les autres questions ouvertes des entrées précédentes restent valables (génération
  de visuels Pillow, export PowerPoint des offres, recherche Meta Graph API, scan d'en-têtes
  HTTP des sites clients, vrai système de comptes staff, flux OAuth Meta/WhatsApp, etc.).

## 2026-09-20 — Infrastructure de tâches planifiées (APScheduler) : Réseaux sociaux + Maintenance

**Contexte** : suite du lot précédent ("réalise le non fait"). L'élément annoncé comme
suivant — l'infrastructure de planification qui débloque plusieurs agents à la fois.

**Infrastructure partagée**
- `platform_core/scheduler.py::create_scheduler()` — un seul `BackgroundScheduler`
  (APScheduler), démarré/arrêté depuis le lifespan FastAPI (`app/main.py`), enregistrant les
  4 jobs ci-dessous. Chaque job ouvre sa propre `Session` SQLAlchemy à chaque exécution
  (jamais partagée entre deux déclenchements) et est enveloppé (`_safe`) pour qu'une
  exception dans un job n'arrête jamais le scheduler entier.
- Vérifié explicitement que le lifespan ne se déclenche pas pendant les tests : la suite
  utilise `TestClient(app)` sans bloc `with` partout, ce qui ne déclenche pas les
  événements de lifespan ASGI (confirmé par un test isolé avant d'écrire le code) — aucun
  job planifié ne tourne donc en arrière-plan pendant `pytest`, testé aussi en conditions
  réelles (`with TestClient(app) as client:` démarre bien le scheduler, l'arrête bien à la
  sortie).
- Piège découvert et corrigé : les colonnes `DateTime` de `platform_core/models.py` sont
  sans fuseau (comportement identique SQLite/PostgreSQL — vérifié empiriquement) : une
  valeur aware assignée à une colonne y perd son tzinfo, à l'écriture comme après relecture
  depuis la base. Comparer un `datetime.now(UTC)` (aware) à une valeur rechargée (naïve)
  lève `TypeError`. Convention adoptée dans `agents/maintenance/scheduled_jobs.py` : une
  fonction `_now_naive_utc()` dédiée pour toute arithmétique contre une colonne de la base,
  gardant `datetime.now(UTC)` (aware) uniquement pour les appels à `agents/maintenance/
  backup.py`, dont les clés R2 sont elles-mêmes parsées en datetimes aware.

**Réseaux sociaux : auto-publication**
- `agents/reseaux_sociaux/agent.py::publish_scheduled_post(post, client)` — logique de
  construction du message + appel Meta, extraite de `app/routers/posts.py` pour être
  réutilisée à l'identique par l'endpoint manuel et par la tâche planifiée.
- `agents/reseaux_sociaux/scheduled_jobs.py::publish_due_posts` — publie tout post
  `scheduled` dont `scheduled_at` est échu (tick de 5 minutes). Échec (page non connectée,
  rejet Meta) → notification staff, une seule par post tant qu'elle n'est pas acquittée (le
  post reste `scheduled`, retenté au tick suivant).

**Maintenance : 3 tâches planifiées, une décision produit tranchée au passage**
- Décision actée (jamais explicitement tranchée avant cette session) : la sauvegarde et le
  scan de sécurité portent sur une ressource **partagée par toute la plateforme** (un seul
  `pg_dump`, un seul `pip-audit`), sans notion par client — leur cadence suit donc
  l'abonnement actif le plus exigeant (Premium > Business > Starter, ce dernier sans scan de
  sécurité), pas une moyenne ni un calcul par client.
- `run_backups_and_retention` : compare l'échéance au dernier `Backup.created_at` réel (pas
  de nouvelle table de log) ; échec → notification critique (`backup_failure`), comme avant.
- `run_security_scans` : compare à la dernière notification `security_finding` — une
  notification "aucune vulnérabilité" est désormais créée même sans trouvaille, uniquement
  pour disposer de cet horodatage (pas de table de log de scan dédiée).
- `run_uptime_checks` : par site, au rythme de l'abonnement actif du client (30 min/5 min/1
  min — "temps réel" Premium approximé faute d'infrastructure de push). 3 champs ajoutés à
  `Site` (`uptime_monitor_id`, `last_uptime_check_at`, `down_since`), comblant l'ancien point
  ouvert "pas encore de champ uptime_monitor_id" (migration `8c6ca4a3abc8`). Notifie une
  seule fois par période d'indisponibilité continue.

**Divers**
- 121 tests au total (contre 107 avant ce lot), tous passent. Packaging non-éditable
  revérifié (nouveau `/tmp/test-install-venv`) : imports, démarrage de l'app et du scheduler
  OK. Smoke-test manuel des 4 jobs contre une vraie base SQLite vide (hors suite de tests).

**Questions ouvertes restantes**
- Planning : rappels de RDV automatiques toujours pas branchés — décision volontairement
  reportée, pas bâclée : nécessite un numéro de contact PME (`Client.contact_phone`
  n'existe pas encore) et des identifiants WhatsApp **au niveau plateforme** (pas ceux du
  client, puisque c'est le staff qui initie le rappel), pas encore modélisés dans
  `platform_core/config.py`. À reprendre comme un lot dédié plutôt que rajouté au forceps
  ici.
- Instrumentation `ActivityEvent` toujours manquante pour Création de site et Réseaux
  sociaux (seul Prospection émet des événements).
- Toutes les autres questions ouvertes des entrées précédentes restent valables.

## 2026-09-20 — Instrumentation ActivityEvent pour Création de site et Réseaux sociaux

**Contexte** : dernier élément de la liste priorisée du lot "réalise le non fait" —
Création de site et Réseaux sociaux n'émettaient encore aucun événement vers le journal
partagé (`platform_core.models.ActivityEvent`), contrairement à Prospection.

- `app/routers/sites.py` : `POST /api/sites`, `.../generate` et `.../publish` journalisent
  respectivement `created`, `content_generated`, `published` (`agent="creation_site"`).
  `.../publish` ne journalise que lors d'une vraie transition (pas sur un appel idempotent
  d'un site déjà publié), cohérent avec le commentaire déjà présent sur l'idempotence.
- `app/routers/posts.py` : les 6 transitions (`created`, `content_generated`,
  `changes_requested`, `validated`, `scheduled`, `published`) journalisent
  (`agent="reseaux_sociaux"`).
- `agents/reseaux_sociaux/scheduled_jobs.py::publish_due_posts` journalise aussi `published`
  (avec `details={"triggered_by": "scheduled_job"}`) pour que le journal reste complet que
  la publication vienne de l'endpoint manuel ou de la tâche planifiée du lot précédent —
  sans ce détail, l'agent Planning ne pourrait pas distinguer les deux origines s'il en a
  besoin plus tard.
- Testé : assertions sur la séquence complète d'événements dans les tests d'API existants
  (`tests/test_sites_api.py`, `tests/test_posts_api.py`) plutôt que des tests séparés — un
  test de flux qui affirme déjà chaque transition HTTP est le bon endroit pour vérifier
  aussi ce qu'elle journalise. Ajouté aussi à `tests/test_scheduled_jobs.py`.
- 121 tests au total (compte inchangé : assertions ajoutées à des tests existants, pas de
  nouveaux tests séparés pour ce lot). Packaging non-éditable revérifié.

**Bilan du lot "réalise le non fait" (3 sessions de travail)** : les deux failles de
sécurité réelles (chiffrement au repos, signature webhook Sentry) sont corrigées ;
l'infrastructure de planification (APScheduler) est en place et branchée sur Réseaux
sociaux + Maintenance ; l'instrumentation `ActivityEvent` couvre désormais 3 agents sur 4
(Maintenance exclu par design, ses actions n'étant pas client-scoped). Restent
explicitement non traités, à reprendre en lots dédiés : rappels de RDV automatiques de
Planning (bloqués sur des décisions de modélisation non encore prises — voir l'entrée
précédente), génération de visuels Pillow, export PowerPoint des offres, recherche Meta
Graph API pour Prospection, scan d'en-têtes HTTP des sites clients, vrai système de comptes
staff, flux OAuth Meta/WhatsApp, synchronisation calendrier externe.

## 2026-09-20 — Décision : rappels de RDV de Planning (contact_phone + WhatsApp plateforme)

**Contexte** : demande explicite de l'utilisateur de trancher ce qui avait été
volontairement laissé en suspens dans l'entrée précédente ("nécessite un numéro de contact
PME et des identifiants WhatsApp au niveau plateforme, pas encore modélisés... à reprendre
comme un lot dédié plutôt que rajouté au forceps").

**Décision actée** : c'est le **staff** de la plateforme qui initie le rappel vers le
client, jamais l'inverse — à l'opposé de l'agent Prospection, où c'est le client qui
contacte ses propres prospects via SON PROPRE compte WhatsApp Business. Ça implique deux
identités WhatsApp Business distinctes qui ne doivent jamais être confondues :
- le compte du **client** (`Client.whatsapp_phone_number_id`/`whatsapp_access_token`,
  existant, utilisé par Prospection) ;
- le compte de la **plateforme elle-même** (nouveau : `settings.platform_whatsapp_
  phone_number_id`/`platform_whatsapp_access_token`), utilisé uniquement par Planning.

Conséquence sur le modèle de données : un nouveau champ `Client.contact_phone` (juste un
numéro, pas un compte WhatsApp Business) — le numéro de la PME que le staff contacte,
renseigné manuellement comme les autres champs de contact du client (`meta_page_id`,
`whatsapp_phone_number_id`...), pas encore de flux de saisie dédié.

**Implémentation**
- `platform_core/models.py` : `Client.contact_phone` (String(50), nullable) et
  `Appointment.reminder_sent_at` (DateTime, nullable — évite les rappels en double).
  Migration `e61cf9c077bd`.
- `platform_core/config.py` : `platform_whatsapp_phone_number_id`/
  `platform_whatsapp_access_token`, vides par défaut (le job ne fait rien tant qu'ils ne
  sont pas configurés, dégradation silencieuse cohérente avec les autres tâches planifiées).
- `agents/planning/scheduled_jobs.py::send_appointment_reminders` — 5ᵉ tâche planifiée
  (APScheduler, tick de 30 minutes), enregistrée dans `platform_core/scheduler.py`. Envoie
  un rappel WhatsApp pour tout RDV `proposed`/`confirmed` dont l'échéance tombe dans les 24h
  (fenêtre fixe, pas encore configurable) et sans rappel déjà envoyé. Réutilise
  `agents.prospection.whatsapp.send_whatsapp_message` (même précédent que Maintenance
  réutilisant le client R2 de Création de site) avec les credentials **plateforme**, pas
  ceux du client. Échec d'envoi → notification staff (une seule par RDV tant qu'elle n'est
  pas acquittée), même principe que `publish_due_posts`.
- Testé : no-op sans credentials plateforme configurés, envoi + marquage
  `reminder_sent_at`, non-duplication au tick suivant, ignoré sans `contact_phone`, ignoré
  hors fenêtre de 24h, notification unique en cas d'échec d'envoi répété.
- 127 tests au total (contre 121 avant ce lot), tous passent. Packaging non-éditable
  revérifié ; smoke-test manuel du job contre une vraie base SQLite vide (sans credentials
  configurés, comportement no-op confirmé).

**Questions ouvertes restantes**
- Fenêtre de rappel fixe (24h) — pas de rappel à plusieurs échéances (ex. J-1 et H-1), pas
  demandé pour l'instant.
- `Client.contact_phone` toujours sans flux de saisie dédié (manuel, comme les autres
  champs de contact).
- Toutes les autres questions ouvertes des entrées précédentes restent valables.
