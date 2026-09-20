# Skills — Agent Création de site

**Mission** : générer un site web pour un client à partir d'un brief (secteur d'activité,
contenu, identité visuelle), en s'appuyant sur des templates par secteur.

**Périmètre** : lit/écrit uniquement les données du site du client concerné (brief, contenu,
structure générée). Ne touche jamais au code ou aux données d'un autre agent (voir
CLAUDE.md §5).

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **API Claude directe** (SDK `anthropic`, modèle `claude-sonnet-5`) | Générer le contenu textuel du site (accroche, présentation, éléments clés) à partir du brief client, en JSON structuré. | **Correction par rapport à CLAUDE.md §3** : le Claude Agent SDK (harnais complet avec accès Bash/fichiers, boucle autonome) est pensé pour des tâches agentiques ouvertes à plusieurs étapes. Générer du contenu à partir d'un brief structuré est un appel unique, pas une exploration ouverte — l'API Claude directe est le bon niveau d'outil, et évite de donner à cet agent un accès Bash/filesystem qu'il n'a aucune raison d'avoir (CLAUDE.md §5, cloisonnement strict). Implémenté dans `agents/creation_site/content.py`. |
| **Jinja2** | Moteur de templates Python pour les gabarits de site par secteur (restaurant, boutique, artisan, services...). | Standard de facto en Python, léger, permet de séparer clairement "template de secteur" (fixe, maintenu par l'équipe) et "contenu généré" (variable, produit par l'agent) — essentiel pour la cohérence visuelle entre clients d'un même pack. |
| **Tailwind CSS** (ou un design system léger équivalent) | Cohérence visuelle et responsive design des sites générés, sans réinventer une bibliothèque de composants par template. | Permet de démarrer vite avec un rendu propre sur mobile — critère important vu l'audience (PME/indépendants consultés majoritairement depuis mobile en Afrique). |
| **Pillow** | Traitement/redimensionnement des images fournies par le client (logo, photos) pour le rendu final du site. | Librairie Python standard, évite les dépendances lourdes pour un besoin simple d'optimisation d'images. |

## Catalogue de templates par secteur (MVP)

Structure commune à tous les templates : header (logo + navigation), section hero
(accroche + appel à l'action), section(s) spécifiques au secteur (ci-dessous), section
Contact (téléphone, WhatsApp, carte de localisation, réseaux sociaux), footer.

| Secteur | Sections spécifiques |
|---|---|
| **Restaurant / restauration rapide** | Menu (catégories + prix), galerie photos, commande/réservation via WhatsApp |
| **Boutique / commerce de détail** | Catalogue produits (grille + prix), bouton commande WhatsApp/paiement mobile |
| **Services beauté & bien-être** (coiffure, esthétique, spa) | Prestations & tarifs, galerie de réalisations, prise de RDV |
| **Artisanat & métiers techniques** (couture, menuiserie, plomberie, électricité...) | Services proposés, galerie de réalisations, zone d'intervention |
| **Services professionnels / conseil** (consultants, comptables, avocats...) | Services, équipe, témoignages clients, prise de RDV |
| **Santé** (cliniques, cabinets, pharmacies) | Spécialités, équipe, horaires/localisation — **contrainte** : aucun contenu médical généré sans validation par un professionnel de santé du client |
| **Hôtellerie & tourisme** (guesthouses, agences de voyage) | Chambres/offres (avec tarifs), galerie photos, réservation |
| **Éducation & formation** (écoles privées, centres de formation) | Programmes/cours proposés, corps enseignant/équipe, inscription |
| **Événementiel** (traiteurs, organisateurs, location de salles) | Prestations/services, portfolio d'événements passés, devis/contact |
| **Générique / vitrine simple** (repli) | Accueil, À propos, Services/Produits, Contact — pour tout secteur non encore couvert |

Secteurs volontairement exclus du MVP (à ajouter plus tard selon la demande réelle des
clients) : agriculture/agroalimentaire, ONG/associations, et tout autre secteur non listé —
ils utilisent le template générique en attendant.

**État d'implémentation des templates** (`agents/creation_site/templates/sectors/`) :
`restaurant` et `generique` sont construits. Les 7 autres secteurs du tableau ci-dessus
utilisent le template générique par repli automatique (`render.py`) en attendant leur design
dédié — c'est du travail de contenu/design restant, pas un manque d'agent logic.

## Génération et publication (tranché)

- **Génération 100% statique (JAMstack)** : chaque site est produit en HTML/CSS statique à
  chaque publication/mise à jour, stocké sur Cloudflare R2 + CDN (CLAUDE.md §3). Pas de
  rendu serveur par page vue : rapide à charger (important vu la connectivité mobile
  variable), peu coûteux à scaler, surface d'attaque réduite.
  - Le besoin de "dynamique" est couvert sans backend par page : formulaire de contact
    soumis en JS vers un endpoint FastAPI dédié (ex. `POST /leads`) qui enregistre le
    message ; réservation/commande via lien direct `wa.me/<numéro>?text=...` (WhatsApp),
    déjà l'usage dominant dans le marché cible.
- **Cycle brouillon → validation → publication**, standard des outils de site-building :
  1. L'agent génère/regénère le site dans un espace de **brouillon** (préfixe `draft/` sur
     R2), jamais directement en production.
  2. Le client consulte l'aperçu via une URL de prévisualisation depuis le dashboard.
  3. Le client valide ("Publier") ou demande des retouches (l'agent régénère le brouillon).
  4. La validation déclenche la promotion du contenu de `draft/` vers `live/` (URL publique
     définitive du client). Aucune mise à jour, initiale ou ultérieure, ne passe en
     production sans ce passage par la validation du client.

## Implémentation actuelle

- `brief.py` : `SiteBrief` (nom, secteur, description, contact) et `Sector` (catalogue).
- `content.py` : `generate_content(brief)` — appel API Claude, validation du JSON retourné
  via `SiteContent` (pydantic), erreur explicite (`ContentGenerationError`) si la réponse ne
  correspond pas au schéma attendu.
- `render.py` : `render_site(brief, content)` — rendu Jinja2, repli automatique vers le
  template générique si le secteur n'a pas encore de template dédié.
- `publish.py` : `write_draft(site_id, html)` — écrit le brouillon **en local** pour
  l'instant (`output/draft/<site_id>/index.html`), en attendant le branchement réel sur
  Cloudflare R2 (voir point ouvert ci-dessous).
- `agent.py` : `generate_draft_site(site_id, brief)` — enchaîne les trois étapes ; le
  contenu structuré (pas le HTML) est la source de vérité stockée en base
  (`platform_core.models.Site.content`), le HTML est régénérable à tout moment.
- Exposé via l'API (`app/routers/sites.py`) : `POST /api/sites` (créer), `POST
  /api/sites/{id}/generate` (générer le brouillon), `GET /api/sites/{id}/preview`
  (prévisualiser), `POST /api/sites/{id}/publish` (valider → `SiteStatus.published`).
- Testé : génération de contenu (avec client Claude simulé, sans appel réseau réel), rendu
  Jinja2, et le flux complet créer→générer→prévisualiser→publier via l'API (voir `tests/`).

## Points à trancher avant implémentation

- Remplacer `write_draft` (écriture locale) par un vrai upload Cloudflare R2 (préfixe
  `draft/<site_id>/`) et implémenter `promote_to_live` (copie `draft/` → `live/` à la
  validation) — nécessite des credentials R2 réels pour être testé, pas fait à ce stade
  (voir TODO dans `publish.py`).
- Authentification/autorisation des endpoints `app/routers/sites.py` : pour l'instant
  n'importe qui peut appeler `/publish` sur n'importe quel site — pas encore de notion
  d'utilisateur/session, à construire avec le reste du dashboard.
- Construire les templates dédiés des 7 secteurs restants (actuellement repli générique).

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : générer le site à partir d'un brief validé, lire/écrire les données du site du
  client concerné.
- Interdit : modifier le code/les données d'un autre agent, publier une version en ligne
  sans processus de validation défini avec l'équipe, utiliser une clé API en dehors de
  `config/credentials/`.
