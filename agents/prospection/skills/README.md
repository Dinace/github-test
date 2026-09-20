# Skills — Agent Prospection commerciale

**Mission** : rechercher des prospects sur des supports publics, créer des fiches prospect,
appliquer un scoring/filtrage, générer des supports visuels d'offre.

**Périmètre** : lit/écrit uniquement les fiches prospects qu'il gère. Ne touche jamais au
code ou aux données d'un autre agent.

## Contrainte de conformité (prioritaire sur tout choix technique)

La recherche de prospects sur des « supports publics » doit respecter :
- les conditions d'utilisation (ToS) des plateformes consultées et leur `robots.txt` ;
- la réglementation applicable en matière de protection des données dans les pays ciblés,
  et le RGPD si des données de ressortissants européens sont concernées ;
- l'interdiction stricte de contacter un prospect classé **"non favorable"** ou
  **"non joignable"** après filtrage (CLAUDE.md §5).

Toute source ou méthode de collecte doit être documentée dans `MEMORY.md` avant d'être
utilisée en production, pour permettre une revue de conformité par l'équipe.

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **httpx / requests + BeautifulSoup** | Collecte de données publiques simples (pages web statiques, annuaires professionnels). | Suffisant pour des sources HTML classiques, léger, largement documenté en Python. |
| **Playwright** | Collecte sur des pages nécessitant du JavaScript (rendu dynamique). | À utiliser seulement si BeautifulSoup ne suffit pas — plus lourd, réservé aux sources qui l'exigent réellement. |
| **API Claude directe** (SDK `anthropic`, modèle `claude-sonnet-5`) | Transformer les données brutes collectées en fiche prospect structurée, et rédiger le message de premier contact. | **Correction** : même raisonnement que les 3 autres agents (agents/creation_site/skills/README.md) — structurer des données ou rédiger un message à partir d'un contexte donné est un appel unique, pas une tâche agentique ouverte ; le Claude Agent SDK n'a pas d'utilité ici. Implémenté dans `agents/prospection/content.py`. |
| **Scoring par règles métier (Python)** | Filtrer/prioriser les prospects (favorable / à qualifier / non favorable / non joignable) selon des critères définis avec l'équipe commerciale. | Un système de règles explicites est plus auditable qu'un modèle ML pour ce stade du projet — important vu l'impact direct sur qui peut être contacté (CLAUDE.md §5). Un modèle de scoring plus avancé pourra être introduit plus tard si le volume le justifie. |
| **ReportLab / python-pptx** | Génération de supports visuels d'offre (PDF ou présentation) à partir d'un gabarit par pack (Starter/Business/Premium). | Librairies Python matures pour générer des documents commerciaux sans dépendance à un outil de design externe. |

## Sources autorisées (tranché — priorité aux API officielles sur le scraping)

Principe : préférer systématiquement une API officielle à la collecte par scraping — plus
robuste, moins fragile aux changements de mise en page, et conforme aux ToS des plateformes
par construction plutôt que par interprétation.

**Sources autorisées :**
- **Google Places API / Google Business Profile** : fiches d'établissement publiques
  (nom, secteur, adresse, téléphone, avis) — source officielle de référence.
- **Meta Graph API** (`META_ADS_TOKEN`/`META_APP_ID`, déjà présents dans les credentials) :
  informations publiques des Pages professionnelles Facebook/Instagram.
- **Annuaires professionnels et registres publics** (ex. chambres de commerce, registre du
  commerce quand l'information est explicitement publique) : collecte HTML classique
  (BeautifulSoup) autorisée, dans le respect du `robots.txt`.

**Sources explicitement interdites :**
- **LinkedIn** : le scraping est interdit par les ToS de la plateforme, quel que soit
  l'outil utilisé (y compris Playwright) — aucune exception.
- **Profils personnels** (Facebook, Instagram...) : hors périmètre, seules les Pages
  professionnelles publiques sont concernées.
- Toute source nécessitant de contourner une authentification, un paywall ou une mesure
  anti-bot.

Cette liste est valable pour le Gabon (pays de lancement) ; toute extension vers un nouveau
pays doit revalider les sources disponibles localement (CLAUDE.md §1).

## Critères de scoring (tranché — règles pondérées, auditables)

Système à 4 catégories déjà actées (CLAUDE.md §5) : **favorable / à qualifier / non
favorable / non joignable**. Critères pondérés proposés :

| Critère | Effet sur le score |
|---|---|
| Coordonnées valides trouvées (téléphone/WhatsApp) | Absence → classement automatique **"non joignable"**, exclusion immédiate (pas de score à calculer). |
| Absence de site web, ou site obsolète/non mobile-friendly | Signal **favorable** fort — correspond exactement à l'offre de la plateforme. |
| A déjà un site professionnel récent et fonctionnel | Signal négatif — besoin déjà couvert. |
| Secteur d'activité correspond à un des templates du catalogue (agent Création de site) | Signal favorable — adéquation avec l'offre. |
| Signaux d'activité récente (avis Google récents, publication récente sur réseaux sociaux, horaires renseignés) | Signal favorable ; absence totale → **"à qualifier"** plutôt que rejeté d'office (donnée insuffisante, pas un rejet). |

Le score final (somme pondérée) détermine la catégorie via des seuils ajustables par
l'équipe commerciale (paramètres, pas codés en dur) — cohérent avec l'exigence
d'auditabilité déjà actée pour ce choix de règles plutôt qu'un modèle ML.

## Canal de première prise de contact (tranché)

**WhatsApp Business** (déjà la clé `WHATSAPP_BUSINESS_TOKEN`), canal dominant dans le
marché cible. Le premier message suit le même principe de validation que l'agent Réseaux
sociaux : un brief/modèle de message doit être validé par un humain avant tout envoi (pas
de prise de contact automatique non supervisée), et jamais vers un prospect "non favorable"
ou "non joignable" (CLAUDE.md §5).

## Implémentation actuelle

- `compliance.py` : `assert_source_allowed(url)` — applique **en code** la règle "LinkedIn
  interdit, sans exception", pas seulement documentée. Toute fonction de collecte HTTP du
  package l'appelle avant la moindre requête (voir `directory_scraper.py`).
- `sources/google_places.py` : `search_places(query)` — recherche via Google Places API
  (New), client HTTP injectable. Note d'honnêteté dans le fichier : schéma de réponse suivi
  au mieux, pas vérifié contre un appel réel faute de clé API disponible dans cette session.
- `directory_scraper.py` : `fetch_directory_page(url)` — collecte HTML basique
  (BeautifulSoup) pour les annuaires publics, garde-fou de conformité systématique.
- `scoring.py` : `score_prospect(signals, weights)` — implémentation réelle du tableau de
  critères ci-dessus. Fonction pure ; poids et seuils sont des paramètres (`ScoringWeights`),
  pas codés en dur, conformément à l'exigence d'ajustabilité déjà actée. Coordonnées
  invalides → `non_joignable` immédiat, sans calcul de score.
- `content.py` : `structure_prospect` (extraction/structuration) et
  `generate_contact_message` (rédaction du premier message WhatsApp) — API Claude directe,
  validation stricte du JSON retourné, erreur explicite si non conforme.
- `whatsapp.py` : `send_whatsapp_message` — envoi réel via WhatsApp Business Cloud API.
  Nécessite `Client.whatsapp_phone_number_id`/`whatsapp_access_token` (renseignés
  manuellement, pas de flux de connexion automatisé — même limite que
  `agents/reseaux_sociaux/meta.py`).
- `offer.py` : `generate_offer_pdf` — génère un PDF d'offre par pack (ReportLab). Choix de
  scope : PDF uniquement pour l'instant, pas de génération PowerPoint (`python-pptx`) tant
  que le besoin n'est pas confirmé.
- `website_audit.py` : `assess_website(url)` — visite réellement le site d'un prospect
  (client HTTP injectable) et retourne un statut heuristique (`none`/`outdated`/`modern`) :
  page injoignable ou HTTP >= 400 → `none` (même besoin qu'un prospect sans site) ; corps
  HTML minimal (< 500 caractères, signature typique d'un domaine parké ou d'une page "en
  construction") ou absence de balise `<meta name="viewport">` (site non pensé mobile,
  signal robuste vu son ancienneté comme standard) → `outdated` ; sinon `modern`. **Note
  d'honnêteté** (même esprit que `security_scan.py`) : c'est une heuristique technique, pas
  un audit de conception/SEO — peut mal classer un cas inhabituel dans les deux sens.
- `agent.py` : `search_and_score` — enchaîne recherche Google Places → dérivation des
  signaux (dont la visite réelle du site via `website_audit.py` quand un `website_uri`
  existe, comble l'ancienne simplification "présence = moderne") → scoring → création des
  fiches en base. `http_client` (recherche Places) et `website_http_client` (visite des
  sites) sont injectables séparément, deux intégrations distinctes avec des besoins de test
  différents. Simplification restante : le secteur est considéré comme correspondant au
  catalogue par construction (la recherche cible déjà un secteur donné).
- Endpoints (`app/routers/prospection.py`), authentifiés par clé API client (comme
  `sites.py`/`posts.py`) : `POST /api/prospects/search`, `GET /api/prospects`, `POST
  /api/prospects/{id}/propose-contact` (**bloqué en code**, 403, si la catégorie est
  `non_favorable`/`non_joignable`, pas seulement documenté), `POST .../validate-contact`,
  `POST .../send-contact` (re-vérifie la catégorie en défense en profondeur + exige la
  connexion WhatsApp, 412 sinon), `GET /api/prospects/{id}/offer` (PDF).
- Testé : conformité (LinkedIn bloqué, y compris en sous-domaine), scoring (les 4
  catégories, seuils configurables), recherche Google Places, détection heuristique du
  statut d'un site (moderne/obsolète/absent, y compris échec réseau et HTTP >= 400),
  structuration/génération de contenu (client Claude simulé), envoi WhatsApp (client HTTP
  simulé), génération de PDF, et le flux complet de contact via l'API (y compris le blocage
  403 sur les catégories interdites) — aucun appel réseau réel dans la suite de tests.

## Points ouverts (pas encore fait, explicitement)

- **Playwright non implémenté** : seules les sources HTML statiques (BeautifulSoup) et
  Google Places sont couvertes ; les sources nécessitant du JavaScript restent à faire si
  le besoin se confirme (skills retenue mais pas codée).
- **Meta Graph API pour la recherche de prospects** (Pages professionnelles) — seul Google
  Places est implémenté pour l'instant ; la clé `META_ADS_TOKEN` existe déjà côté Réseaux
  sociaux mais son usage côté Prospection reste à construire.
- **python-pptx** non implémenté — seul le PDF (ReportLab) existe.
- **Flux de connexion WhatsApp Business** (comme pour Meta) — credentials renseignés
  manuellement en attendant.
- Vérification de connectivité réelle : Google Places et WhatsApp Cloud API n'ont jamais été
  appelés contre de vrais services dans cette session (pas de clés disponibles) — seule la
  logique est testée avec des doublures. Idem pour `website_audit.py` : l'heuristique n'a
  jamais visité de vrai site dans cette session.

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : rechercher des prospects sur des supports publics conformes, créer des fiches,
  scorer/filtrer, générer des supports visuels d'offre.
- Interdit : contacter un prospect classé "non favorable" ou "non joignable", modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
