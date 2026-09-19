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
