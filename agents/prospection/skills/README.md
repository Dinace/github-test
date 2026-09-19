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

## Points à trancher avant implémentation

- Liste précise des sources publiques autorisées (validée avec l'équipe côté conformité
  légale, pays par pays si nécessaire).
- Critères exacts du scoring (favorable / à qualifier / non favorable / non joignable) et
  qui les définit.
- Canal de première prise de contact (WhatsApp Business, email...) et son propre processus
  de validation.

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : rechercher des prospects sur des supports publics conformes, créer des fiches,
  scorer/filtrer, générer des supports visuels d'offre.
- Interdit : contacter un prospect classé "non favorable" ou "non joignable", modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
