# Skills — Agent Planning (suivi & rendez-vous)

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

**Périmètre** : lecture seule sur les données des 4 autres agents (Site, Post, Prospect) —
jamais d'écriture dans leur périmètre propre (CLAUDE.md §5). Écrit uniquement dans ses
propres tables (`Appointment`) et dans le journal d'événements partagé (`ActivityEvent`,
où chaque agent ne journalise que ses propres actions).

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **Requêtes SQLAlchemy classiques** (pas de nouvelle librairie) | Agréger les tables déjà possédées par les autres agents (Site, Post, Prospect) en un résumé par client. | Aucune dépendance supplémentaire nécessaire : c'est de la lecture agrégée sur des données déjà structurées, pas un besoin d'outil externe. Garde le cloisonnement simple (lecture seule, jamais d'écriture croisée). |
| **Journal d'événements applicatif explicite** (`platform_core.activity.log_event`, table dédiée) | Reconstituer l'historique du pipeline d'un prospect dans le temps, que le statut courant seul ne conserve pas. | Préféré à un outil de versioning automatique (ex. SQLAlchemy-Continuum, qui journalise tout changement de colonne) : plus simple, plus lisible, et ne journalise que les événements métier pertinents plutôt que chaque mutation SQL. Vit dans `platform_core` (partagé) plutôt que dans un agent, car plusieurs agents y écrivent. |
| **API Claude directe** (SDK `anthropic`, modèle `claude-sonnet-5`) | Transformer un résumé structuré (compteurs) en 2-3 phrases de synthèse pour l'équipe. | Même raisonnement que les 4 autres agents : transformer des données structurées en texte est un appel unique, pas une tâche agentique ouverte — pas le Claude Agent SDK. |
| **FastAPI (déjà en place)** | Exposer deux niveaux d'accès distincts : staff (jeton d'opération) et client (clé API). | Aucune nouvelle dépendance ; réutilise le même mécanisme d'auth que Maintenance (staff) et que Création de site/Réseaux sociaux/Prospection (client). |
| **`agents.prospection.whatsapp` (réutilisé, pas dupliqué)** | Rappel de RDV par WhatsApp (`scheduled_jobs.py::send_appointment_reminders`). | Le module existe déjà et fonctionne (voir agents/prospection/skills/README.md) ; le réutiliser suit le même précédent que Maintenance réutilisant le client R2 de Création de site — un seul module par intégration technique, pas une copie par agent. |
| **APScheduler** (partagé, voir `platform_core/scheduler.py`) | Déclenche `send_appointment_reminders` automatiquement (tick de 30 minutes). | Même infrastructure que Réseaux sociaux/Maintenance, pas une planification propre à Planning. |

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

## Rappel des permissions

- Autorisé : lire les données des 4 autres agents pour les agréger (jamais les modifier),
  journaliser ses propres événements, gérer les rendez-vous staff/client.
- Interdit : modifier le code ou les données propres d'un autre agent (CLAUDE.md §5), créer
  des événements au nom d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
