# Skills — Agent Réseaux sociaux

**Mission** : générer du contenu (textes, visuels), planifier un calendrier de publication,
et publier via les API des réseaux sociaux (Meta, WhatsApp Business) — uniquement sur
validation préalable d'un brief ou d'un contenu (voir CLAUDE.md §5, règle stricte : aucune
publication sans validation).

**Périmètre** : lit/écrit uniquement le contenu réseaux sociaux du client concerné. Ne
touche jamais au code ou aux données d'un autre agent.

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **API Claude directe** (SDK `anthropic`, modèle `claude-sonnet-5`) | Rédaction des textes de publication (posts, légendes) à partir du brief et du ton de marque du client. | **Correction** : même raisonnement que l'agent Création de site (CLAUDE.md §3) — générer un texte à partir d'un brief structuré est un appel unique, pas une tâche agentique ouverte ; le Claude Agent SDK (accès Bash/fichiers) n'a pas d'utilité ici et élargirait le périmètre de l'agent sans raison. Implémenté dans `agents/reseaux_sociaux/content.py`. |
| **Meta Graph API** (`META_ADS_TOKEN`, `META_APP_ID/SECRET`) | Publication et gestion de campagnes sur Facebook/Instagram. | API officielle, seule voie légitime pour publier au nom du client ; nécessaire pour respecter les conditions d'utilisation des plateformes. |
| **WhatsApp Business API** (`WHATSAPP_BUSINESS_TOKEN`) | Messages clients (confirmations, notifications), catalogue produit si applicable. | Canal de communication le plus utilisé par les PME/indépendants dans le marché cible ; API officielle obligatoire pour un usage professionnel conforme. |
| **APScheduler / Celery beat** | Planification du calendrier de publication (dates/heures programmées). | Solution standard en Python pour des tâches planifiées ; Celery beat si l'infrastructure prévoit déjà une file de tâches (ex. pour la Maintenance), sinon APScheduler pour un besoin plus léger. |
| **Pillow** (+ gabarits graphiques) | Génération de visuels simples (bannières, citations, promos) à partir d'un template de marque par client. | Suffisant pour des visuels basiques sans dépendance à un service tiers payant ; à réévaluer si un besoin de design plus avancé émerge (ex. API Canva). |

## Format du brief et workflow de validation (tranché)

**Brief structuré**, un objet par contenu prévu :
- objectif (ex. promotion, annonce, engagement) ;
- ton/voix — repris du profil de marque du client, défini une fois à l'onboarding ;
- éléments obligatoires (offre/prix/date si promo, mentions légales si nécessaire) ;
- visuel — généré par l'agent (Pillow) ou fourni par le client ;
- date/heure de publication souhaitée.

**Workflow de validation**, statuts successifs (aucun raccourci possible) :
1. `brouillon` — l'agent génère le contenu à partir du brief.
2. `en attente de validation` — le client est notifié (dashboard + WhatsApp).
3. `validé` — le client approuve tel quel, ou l'agent régénère après une demande de
   modification (retour à `brouillon`).
4. `planifié` puis `publié` — seul un contenu `validé` peut entrer dans la file de
   publication planifiée (APScheduler/Celery beat) ; la transition `validé` → `publié` est
   la seule qui déclenche un appel réel à l'API Meta/WhatsApp.

Traçabilité : chaque changement de statut (qui, quand, quoi) est stocké en base
(PostgreSQL) avec le contenu concerné — pas dans `MEMORY.md`, qui reste réservé au journal
de décisions techniques du projet, pas aux données clients.

## Portée initiale (tranché)

MVP : **Meta Graph API + WhatsApp Business API** uniquement (cohérent avec les packs
Business/Premium, CLAUDE.md §1). Google Business Profile reste rattaché à l'agent Création
de site (fiche établissement) ; Google Ads est différé après le MVP tant que la demande
n'est pas confirmée — la clé reste documentée dans `config/credentials/` sans être activée.

## Implémentation actuelle

- `brief.py` : `PostBrief` (objectif, éléments obligatoires, date de publication souhaitée,
  visuel fourni ou non) et `PostObjective` (catalogue : promotion, annonce, engagement).
- `content.py` : `generate_content(brief, brand_voice)` — appel API Claude, validation du
  JSON retourné via `PostContent` (pydantic), erreur explicite si non conforme. Le ton de
  marque (`Client.brand_voice`, défini une fois) est transmis à chaque génération.
- `meta.py` : `publish_to_meta(page_id, access_token, message)` — publication réelle d'un
  post texte sur une Page Meta (Graph API, via `httpx`), avec `MetaPublishError` explicite
  en cas d'échec HTTP. **WhatsApp non implémenté** : ce n'est pas une "publication" au sens
  réseau social mais un canal de messagerie basé sur l'opt-in et des templates approuvés —
  un flux différent, volontairement pas fait à moitié ici.
- `agent.py` : `generate_draft_content(brief, brand_voice)` — délègue à `content.py` ; pas
  de rendu/stockage de fichier à orchestrer en plus, contrairement à l'agent Création de
  site (le contenu texte est directement la source de vérité stockée en base).
- Exposé via l'API, authentifié par clé API (`app/routers/posts.py`) : `POST /api/posts`
  (créer), `POST /api/posts/{id}/generate` (générer), `POST /api/posts/{id}/request-changes`
  (retour à brouillon), `POST /api/posts/{id}/validate`, `POST /api/posts/{id}/schedule`
  (fixe `scheduled_at`), `POST /api/posts/{id}/publish` (appel Meta réel — 412 si le client
  n'a pas connecté sa Page Meta). Chaque transition de statut est vérifiée strictement
  (409 si l'action ne correspond pas au statut courant) — aucun raccourci possible, comme
  décidé ci-dessus.
- Connexion Meta du client : `Client.meta_page_id` / `Client.meta_page_access_token`,
  renseignés manuellement pour l'instant (voir points ouverts). Le token est chiffré au
  repos (`platform_core.models.EncryptedString`, voir `platform_core/encryption.py`) —
  transparent pour ce module, qui continue de lire/écrire du texte en clair côté code.
- Testé : génération de contenu (client Claude simulé), publication Meta (client HTTP
  simulé), et le flux complet create→generate→request-changes→generate→validate→schedule→
  publish via l'API (voir `tests/`) — aucun appel réseau réel dans la suite de tests.

## Points à trancher avant implémentation

- Flux OAuth de connexion Meta (Facebook Login, sélection de Page, échange/rafraîchissement
  de token longue durée) — pas implémenté, `meta_page_id`/`meta_page_access_token` doivent
  être renseignés manuellement en attendant.
- Vraie planification automatique (APScheduler/Celery beat) : `POST .../schedule` fixe
  `scheduled_at` en base, mais rien ne déclenche encore `publish` automatiquement à cette
  date — actuellement un appel manuel à `/publish`, une tâche planifiée reste à construire.
- Génération de visuels (Pillow) — pas implémentée, `visual_provided_by_client` existe dans
  le brief mais rien ne consomme un visuel généré ou fourni pour l'instant.
- WhatsApp Business : flux de messagerie (opt-in, templates approuvés) à concevoir
  séparément, différent d'une "publication" (voir `meta.py`).

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : générer du contenu à partir d'un brief, planifier des publications, publier
  **uniquement** si un brief ou une validation existe pour ce contenu précis.
- Interdit : publier sans validation préalable, modifier le code/les données d'un autre
  agent, utiliser une clé API en dehors de `config/credentials/`.
