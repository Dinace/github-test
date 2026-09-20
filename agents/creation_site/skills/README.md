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

**État d'implémentation des templates** (`agents/creation_site/templates/sectors/`) : les 10
templates du catalogue sont construits (les 9 secteurs + le générique de repli). Chacun
réutilise la structure commune (`base.html.jinja`) avec un libellé de section adapté au
secteur (ex. "Notre menu" pour restaurant, "Nos produits" pour boutique). Le repli
automatique vers le générique reste actif comme filet de sécurité (`render.py`) si un
secteur venait à perdre son template dédié.

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
  template générique si le secteur n'a pas de template dédié.
- `storage.py` : `upload_draft(site_id, html)` / `promote_to_live(site_id)` — upload réel
  vers Cloudflare R2 (API compatible S3 via `boto3`), préfixes `draft/<site_id>/` et
  `live/<site_id>/`. Client S3 injectable pour les tests (pas de credentials réels requis
  pour lancer la suite).
- `agent.py` : `generate_draft_site(site_id, brief)` — enchaîne les trois étapes ; le
  contenu structuré (pas le HTML) est la source de vérité stockée en base
  (`platform_core.models.Site.content`), le HTML est régénérable à tout moment.
- Exposé via l'API, avec authentification par clé API (voir ci-dessous) :
  `app/routers/sites.py` — `POST /api/sites` (créer), `POST /api/sites/{id}/generate`
  (générer le brouillon), `GET /api/sites/{id}/preview` (prévisualiser), `POST
  /api/sites/{id}/publish` (valider → promotion R2 `draft/` → `live/` →
  `SiteStatus.published`). Chacune de ces trois actions (hors prévisualisation, en lecture
  seule) journalise un événement (`platform_core.activity.log_event`, catégories `created`/
  `content_generated`/`published`) lu par l'agent Planning pour son résumé transverse.
- Testé : génération de contenu (client Claude simulé), rendu Jinja2 (les 10 templates +
  filet de sécurité de repli), stockage R2 (client S3 simulé), authentification (génération/
  vérification de clé), et le flux complet créer→générer→prévisualiser→publier via l'API,
  y compris la journalisation d'événements (voir `tests/`) — aucun appel réseau réel dans la
  suite de tests.

## Authentification et cloisonnement (tranché)

- **Clé API par client** (`platform_core/auth.py`) : clé aléatoire à haute entropie
  (`secrets.token_urlsafe`), hachée en SHA-256 avant stockage (`Client.api_key_hash`).
  SHA-256 est correct ici — pas bcrypt/argon2 — car la clé est déjà un secret à haute
  entropie généré par la plateforme, pas un mot de passe humain à faible entropie.
- `POST /api/clients` crée un client et retourne sa clé API **une seule fois** (convention
  standard, comme Stripe/GitHub) — jamais récupérable ensuite.
- Tous les endpoints `app/routers/sites.py` exigent `Authorization: Bearer <clé API>`
  (`app/auth.py::get_current_client`) et vérifient que le site demandé appartient bien au
  client authentifié (`_get_owned_site`, 403 sinon) — c'est le cloisonnement strict entre
  clients exigé par CLAUDE.md §5, pas seulement entre agents.
- **Portée volontairement limitée** : ceci authentifie un *client* de la plateforme pour ses
  propres endpoints, pas un login humain avec session pour le dashboard (formulaire de
  connexion, mot de passe, "mot de passe oublié"...) — ce dernier reste à concevoir
  séparément et pourra s'appuyer sur ce même modèle `Client`.

## Points à trancher avant implémentation

- Login humain pour le dashboard (au-delà de la clé API machine-à-machine ci-dessus) : reste
  à concevoir avec le reste du dashboard (CLAUDE.md §3, HTMX/Jinja2/Alpine).
- Vérification de connectivité réelle à R2 : le code d'upload est écrit et testé avec un
  client S3 simulé, mais n'a pas été exécuté contre un vrai bucket R2 (credentials non
  disponibles à ce stade) — à valider dès que `config/credentials/.env` est renseigné.

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : générer le site à partir d'un brief validé, lire/écrire les données du site du
  client concerné.
- Interdit : modifier le code/les données d'un autre agent, publier une version en ligne
  sans processus de validation défini avec l'équipe, utiliser une clé API en dehors de
  `config/credentials/`.
