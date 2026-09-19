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
| **Claude Agent SDK — extraction/structuration** | Transformer les données brutes collectées en fiche prospect structurée (nom, secteur, contact, besoins probables). | Cohérent avec l'orchestration globale du projet ; utile pour normaliser des données hétérogènes selon la source. |
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

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : rechercher des prospects sur des supports publics conformes, créer des fiches,
  scorer/filtrer, générer des supports visuels d'offre.
- Interdit : contacter un prospect classé "non favorable" ou "non joignable", modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
