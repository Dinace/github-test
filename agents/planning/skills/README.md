# Skills — Agent Planning (suivi, rendez-vous & mise en place de l'offre)

**Statut particulier** : contrairement aux 4 agents de CLAUDE.md §2, Planning n'est **pas un
agent vendu dans les packs** (Starter/Business/Premium, CLAUDE.md §1). C'est un outil
interne à l'équipe qui opère la plateforme, avec une vue limitée exposée au client. Décision
actée avec l'utilisateur :
- **Suivi** : vue d'ensemble transverse de l'activité de chaque client à travers les 4
  agents, et historique du pipeline de chaque prospect dans le temps.
- **Rendez-vous** : entre l'équipe de la plateforme (staff) et les clients PME (onboarding,
  suivi commercial, support) — **pas** un module de prise de RDV grand public pour les
  clients finaux du PME (ex. réservation restaurant), qui resterait un besoin distinct non
  couvert ici.
- **"Office manager"** (suivi des étapes de mise en place de l'offre + notification précise
  des équipes internes concernées) : demandé initialement comme "un agent office manager"
  séparé — **décision actée avec l'utilisateur : une extension du périmètre de Planning
  plutôt qu'un 6ᵉ agent**, Planning faisant déjà du suivi transverse de l'activité client ;
  créer un agent distinct aurait recoupé sa mission sans bénéfice clair. Reste, comme
  Planning, interne et hors packs (l'audience — "les commerciaux et autres services" — est
  l'équipe qui opère la plateforme, jamais le client). Inclut la **collecte sécurisée des
  accès réseaux** du client (Meta, WhatsApp Business) et une **vue agrégée des informations
  utiles au projet** — deux points précisés avec l'utilisateur : les "accès réseaux"
  désignent les identifiants déjà modélisés (pas un nouveau périmètre de types de credential
  à inventer), et les "infos projet" sont l'agrégation de l'existant plus une note libre,
  pas une nouvelle structure de données par catégorie.

**Périmètre** : lecture seule sur les données des 4 autres agents (Site, Post, Prospect) —
jamais d'écriture dans leur périmètre propre (CLAUDE.md §5). Écrit uniquement dans ses
propres tables (`Appointment`, `OnboardingNotification`) et dans le journal d'événements
partagé (`ActivityEvent`, où chaque agent ne journalise que ses propres actions).

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **Requêtes SQLAlchemy classiques** (pas de nouvelle librairie) | Agréger les tables déjà possédées par les autres agents (Site, Post, Prospect) en un résumé par client. | Aucune dépendance supplémentaire nécessaire : c'est de la lecture agrégée sur des données déjà structurées, pas un besoin d'outil externe. Garde le cloisonnement simple (lecture seule, jamais d'écriture croisée). |
| **Journal d'événements applicatif explicite** (`platform_core.activity.log_event`, table dédiée) | Reconstituer l'historique du pipeline d'un prospect dans le temps, que le statut courant seul ne conserve pas. | Préféré à un outil de versioning automatique (ex. SQLAlchemy-Continuum, qui journalise tout changement de colonne) : plus simple, plus lisible, et ne journalise que les événements métier pertinents plutôt que chaque mutation SQL. Vit dans `platform_core` (partagé) plutôt que dans un agent, car plusieurs agents y écrivent. |
| **API Claude directe** (SDK `anthropic`, modèle `claude-sonnet-5`) | Transformer un résumé structuré (compteurs) en 2-3 phrases de synthèse pour l'équipe. | Même raisonnement que les 4 autres agents : transformer des données structurées en texte est un appel unique, pas une tâche agentique ouverte — pas le Claude Agent SDK. |
| **FastAPI (déjà en place)** | Exposer deux niveaux d'accès distincts : staff (jeton d'opération) et client (clé API). | Aucune nouvelle dépendance ; réutilise le même mécanisme d'auth que Maintenance (staff) et que Création de site/Réseaux sociaux/Prospection (client). |
| **`agents.prospection.whatsapp` (réutilisé, pas dupliqué)** | Rappel de RDV par WhatsApp (`scheduled_jobs.py::send_appointment_reminders`). | Le module existe déjà et fonctionne (voir agents/prospection/skills/README.md) ; le réutiliser suit le même précédent que Maintenance réutilisant le client R2 de Création de site — un seul module par intégration technique, pas une copie par agent. |
| **APScheduler** (partagé, voir `platform_core/scheduler.py`) | Déclenche `send_appointment_reminders` et `notify_onboarding_progress` automatiquement (tick de 30 minutes). | Même infrastructure que Réseaux sociaux/Maintenance, pas une planification propre à Planning. |
| **Requêtes SQLAlchemy classiques, encore** (`onboarding.py`) | Calculer la progression de la mise en place de l'offre à partir de l'état courant (Site/Post/Prospect/Backup/Subscription), sans nouvelle source de vérité. | Même raisonnement que `dashboard.py` (première ligne du tableau) : c'est de la lecture agrégée, pas un besoin d'outil externe — une étape n'est jamais "vraie" par elle-même, toujours dérivée de ce que possèdent déjà les autres agents. |
| **`EncryptedString` (déjà en place, `platform_core/encryption.py`)** | Chiffrement au repos des accès réseaux collectés (`network_access.py`). | Réutilise le mécanisme déjà retenu pour `Client.meta_page_access_token`/`whatsapp_access_token` (lot sécurité d'une session précédente) — ces mêmes colonnes, pas une nouvelle table ni un nouveau mécanisme de chiffrement. |

**Écarté pour l'instant** : un vrai outil de calendrier (Google Calendar API, Calendly...)
pour la synchronisation du côté staff — le besoin actuel (RDV internes, volume faible) ne le
justifie pas ; à réévaluer si le volume de RDV staff augmente significativement.

## Implémentation actuelle

- `platform_core/activity.py` + `platform_core.models.ActivityEvent` : journal partagé,
  alimenté par Prospection (`created`, `contact_proposed`, `contact_validated`,
  `contact_sent`), Création de site (`created`, `content_generated`, `published`) et Réseaux
  sociaux (`created`, `content_generated`, `changes_requested`, `validated`, `scheduled`,
  `published` — y compris depuis la tâche planifiée d'auto-publication, pas seulement les
  endpoints manuels). Maintenance n'émet volontairement rien ici : ses actions sont
  déclenchées par le staff ou par des tâches planifiées, pas par un client à travers son
  propre pipeline d'activité (voir points ouverts).
- `dashboard.py` : `get_client_activity_summary(client_id)` — compte les sites en brouillon
  avec contenu généré, les posts en attente de validation, les prospects à qualifier et les
  prospects en attente de validation de contact.
- `pipeline.py` : `get_prospect_pipeline(prospect_id)` — historique chronologique des
  événements d'un prospect.
- `appointments.py` : `propose_appointment` / `confirm_appointment` / `cancel_appointment` /
  `complete_appointment` — cycle de vie complet d'un RDV.
- `digest.py` : `generate_digest(summary)` — synthèse en langage naturel du résumé
  d'activité, via l'API Claude.
- Endpoints (`app/routers/planning.py`), deux routeurs séparés avec deux niveaux d'accès :
  - **Staff** (`OPS_API_TOKEN`, même stopgap que Maintenance) : résumé et synthèse de
    n'importe quel client, pipeline de n'importe quel prospect, proposer/lister/clôturer
    des RDV.
  - **Client** (clé API propre) : son propre résumé, ses propres RDV, confirmer/annuler
    (avec vérification de propriété, comme les autres agents).
- Testé : journalisation d'événements, agrégation du résumé (y compris le piège
  SQLAlchemy découvert et corrigé ci-dessous), historique de pipeline, cycle de vie complet
  d'un RDV, synthèse (Claude simulé), et les deux routeurs via l'API — aucun appel réseau
  réel dans la suite de tests.
- `scheduled_jobs.py::send_appointment_reminders` : tâche planifiée (APScheduler, voir
  `platform_core/scheduler.py`, tick de 30 minutes) qui envoie un rappel WhatsApp pour tout
  rendez-vous `proposed`/`confirmed` dont l'échéance tombe dans les 24h et n'a pas déjà reçu
  de rappel (`Appointment.reminder_sent_at`). Décision actée dans cette session (jusqu'ici
  explicitement en attente) : c'est le **staff** qui contacte le client, jamais l'inverse —
  ce qui nécessitait deux informations qui n'existaient pas encore :
  - `Client.contact_phone` : le numéro de contact de la PME (renseigné manuellement, comme
    les autres champs de contact du client) — distinct de `Client.whatsapp_phone_number_id`
    (le compte WhatsApp Business DU CLIENT, utilisé par Prospection pour que ce client
    contacte SES PROPRES prospects) ;
  - `settings.platform_whatsapp_phone_number_id`/`platform_whatsapp_access_token` : le
    compte WhatsApp Business de la **plateforme elle-même**, puisque c'est l'équipe qui
    parle en son nom propre, pas au nom d'un client.
  Aucune des deux configurée → le job ne fait rien (dégradation silencieuse, cohérente avec
  les autres tâches planifiées sans credentials). Échec d'envoi → notification staff (une
  seule par rendez-vous tant qu'elle n'est pas acquittée), même principe que
  `agents/reseaux_sociaux/scheduled_jobs.py::publish_due_posts`.
- `onboarding.py::get_onboarding_checklist(client_id)` — "office manager" : liste ordonnée
  des étapes de mise en place de l'offre pour ce client, **calculées** (jamais un nouvel
  état écrit ailleurs) à partir de Site/Post/Prospect/Backup/Subscription :
  - `site_created` / `site_content_generated` / `site_published` — toujours présentes
    (Création de site est dans tous les packs) ;
  - `first_backup_confirmed` — sauvegarde plateforme, pas par client (voir
    `platform_core.models.Backup`) : franchie pour tous les clients dès qu'UNE sauvegarde
    existe, décision cohérente avec celle déjà actée pour la cadence de sauvegarde
    (`agents/maintenance/scheduled_jobs.py`) ;
  - `social_media_active` / `prospection_started` — uniquement pour les packs
    Business/Premium (Réseaux sociaux et Prospection absents du Starter, CLAUDE.md §1) :
    inutile de notifier une étape que ce client n'a pas achetée.
  Chaque étape porte une `team` cible (`commercial` ou `technique`).
- `scheduled_jobs.py::notify_onboarding_progress` : tâche planifiée (tick de 30 minutes) qui
  parcourt les clients avec un abonnement actif, calcule leur checklist, et crée **une seule**
  `OnboardingNotification` par (client, étape) la première fois qu'elle est franchie —
  l'existence de la notification sert elle-même de marqueur "déjà notifié" (une étape ne
  redevient jamais non franchie).
- `platform_core.models.OnboardingNotification` — modèle **distinct** de
  `platform_core.models.Notification` (celle de l'agent Maintenance) : audiences et
  périmètres différents (commercial/technique vs anomalies techniques), et les mélanger
  aurait violé le cloisonnement (`Notification` est possédée par Maintenance).
- Endpoints ajoutés à `app/routers/planning.py` :
  - **Staff** : `GET /clients/{id}/onboarding` (checklist d'un client), `GET /notifications`
    (filtrable `?team=commercial|technique` — c'est concrètement ce que "notifier les
    commerciaux et autres services de manière précise" recouvre : chaque service ne voit
    que ce qui le concerne), `POST /notifications/{id}/acknowledge`.
  - **Client** : `GET /me/onboarding` (sa propre checklist).
- Testé : checklist par pack (Starter sans les étapes Réseaux sociaux/Prospection, Business
  avec), progression reflétée quand Site/Post/Prospect/Backup changent d'état, tâche
  planifiée (création une seule fois par étape, routage vers la bonne équipe, ignore les
  clients sans abonnement actif), et les endpoints via l'API (staff et client) — aucun appel
  réseau réel dans la suite de tests.
- `network_access.py::set_network_access` / `get_network_access_status` — collecte
  sécurisée des accès réseaux du client : écrit dans les champs déjà existants sur
  `Client` (`meta_page_id`/`meta_page_access_token`, `whatsapp_phone_number_id`/
  `whatsapp_access_token`, chiffrés au repos via `EncryptedString`), jusqu'ici renseignés
  uniquement à la main en base faute de point de collecte applicatif. **Write-only par
  conception** : `NetworkAccessStatus` (la seule valeur jamais retournée) ne contient que
  des booléens `meta_connected`/`whatsapp_connected`, jamais la valeur en clair d'un token
  — même principe que `Client.api_key_hash` (`platform_core/auth.py`), un secret soumis ne
  redevient jamais lisible via l'API. Mise à jour partielle : ne fournir que le champ à
  changer (ex. rotation d'un seul token) n'efface pas les autres. Écrire dans `Client`
  (modèle **partagé**, pas "possédé" par Réseaux sociaux ou Prospection) reste cohérent
  avec le cloisonnement (CLAUDE.md §5).
- `project_info.py::get_project_info` / `update_project_notes` — vue agrégée des
  informations utiles au projet : regroupe ce qui existe déjà (nom/secteur/`Client`,
  description du brief le plus récent de `Site`, ton de marque, contact, statut des accès
  réseaux ci-dessus) plutôt que de dupliquer une nouvelle source de vérité, plus
  `Client.project_notes` (note libre, propre à ce module, jamais montrée au client).
- Endpoints staff supplémentaires : `GET /clients/{id}/project-info`,
  `PUT /clients/{id}/notes`, `PUT /clients/{id}/network-access` (write-only, voir
  ci-dessus — testé explicitement qu'aucune réponse ne contient jamais la valeur d'un
  token soumis).
- Testé (accès réseaux/infos projet) : statut déconnecté par défaut, connexion reflétée
  après soumission, mise à jour partielle sans effacer les autres champs, chiffrement au
  repos (valeur brute en base différente du texte soumis), agrégation correcte avec/sans
  site existant, note libre persistée, et les 3 endpoints via l'API — y compris une
  assertion explicite qu'un token soumis n'apparaît jamais dans la réponse HTTP.

## Bug découvert et corrigé pendant l'implémentation

`Site.content.isnot(None)` (utilisé par `dashboard.py` pour ne compter que les sites avec
du contenu généré) ne filtrait rien : SQLAlchemy stocke par défaut un `None` Python dans une
colonne `JSON` comme un littéral JSON `"null"`, **pas** un vrai `NULL` SQL — donc
`IS NOT NULL` ne l'excluait jamais. Corrigé à la racine dans `platform_core/models.py`
(`JSON(none_as_null=True)`), ce qui rend aussi ce comportement correct pour
`Post.content`/`Prospect.contact_message`, qui utilisent le même type partagé `_JSONB`.

## Points ouverts (pas encore fait, explicitement)

- Le résumé transverse (`dashboard.py`) reste basé sur une lecture directe des tables
  Site/Post/Prospect, pas sur `ActivityEvent` — cohérent avec ce que journalise chaque
  agent aujourd'hui (Maintenance n'émet toujours rien, ses actions n'étant pas initiées par
  un client), mais les deux mécanismes (lecture directe vs journal d'événements) devront
  converger si `dashboard.py` a un jour besoin de l'historique, pas seulement du compte
  courant.
- Synchronisation avec un vrai calendrier externe (Google Calendar) côté staff.
- Pas de fenêtre de rappel configurable (fixée à 24h avant l'échéance, voir
  `scheduled_jobs.py::_REMINDER_WINDOW`) — un rappel à plusieurs échéances (ex. J-1 et H-1)
  n'a pas été demandé, à construire si le besoin se confirme.
- `Client.contact_phone` renseigné manuellement, pas de flux de saisie dédié (même limite
  que `meta_page_id`/`whatsapp_phone_number_id` pour les autres agents).
- Pas de compte staff individuel (même limite que `OPS_API_TOKEN` pour Maintenance) :
  `staff_contact` est un champ texte libre, pas une identité vérifiée.
- Checklist "office manager" figée dans le code (`onboarding.py`), pas configurable par
  l'équipe (contrairement au scoring de Prospection, qui expose des poids ajustables) —
  à revoir si les étapes doivent souvent changer.
- Pas de canal de notification réel (email/Slack) pour les équipes commercial/technique :
  les `OnboardingNotification` sont surfacées uniquement via l'API
  (`GET /api/planning/notifications`), à consulter activement — même limite que les
  `Notification` de l'agent Maintenance.
- Étape `first_backup_confirmed` commune à tous les clients (sauvegarde plateforme, pas par
  client) : un nouveau client bascule instantanément sur cette étape dès qu'une sauvegarde
  existe déjà pour la plateforme, ce qui est honnête (ses données EN font partie) mais peu
  informatif comme signal d'onboarding individuel — à revoir si un signal plus spécifique
  au client est nécessaire.
- Collecte des accès réseaux limitée à Meta/WhatsApp (les seuls déjà modélisés sur
  `Client`, décision actée avec l'utilisateur) — pas d'hébergement/domaine ni d'autres
  réseaux sociaux, ce qui nécessiterait une structure de stockage générique (type de
  credential + valeur chiffrée) non construite ici.
- `PUT /clients/{id}/network-access` ne vérifie pas la validité du token soumis (ex. appel
  test à l'API Meta/WhatsApp) — un token expiré ou mal copié n'est détecté qu'au premier
  usage réel par Réseaux sociaux/Prospection, pas à la soumission.

## Rappel des permissions

- Autorisé : lire les données des 4 autres agents pour les agréger (jamais les modifier),
  journaliser ses propres événements, gérer les rendez-vous staff/client, notifier les
  équipes internes de la progression de la mise en place de l'offre, collecter et stocker
  de façon chiffrée les accès réseaux du client dans les champs partagés de `Client`.
- Interdit : modifier le code ou les données propres d'un autre agent (CLAUDE.md §5), créer
  des événements au nom d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
