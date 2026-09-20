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
| **`agents.prospection.whatsapp` (réutilisé, pas dupliqué)** | Rappel de RDV par WhatsApp (extension future, pas encore branchée). | Le module existe déjà et fonctionne (voir agents/prospection/skills/README.md) ; le réutiliser suit le même précédent que Maintenance réutilisant le client R2 de Création de site — un seul module par intégration technique, pas une copie par agent. |

**Écarté pour l'instant** : un vrai outil de calendrier (Google Calendar API, Calendly...)
pour la synchronisation du côté staff — le besoin actuel (RDV internes, volume faible) ne le
justifie pas ; à réévaluer si le volume de RDV staff augmente significativement.

## Implémentation actuelle

- `platform_core/activity.py` + `platform_core.models.ActivityEvent` : journal partagé,
  alimenté pour l'instant uniquement par l'agent Prospection (`created`, `contact_proposed`,
  `contact_validated`, `contact_sent`) — les 3 autres agents n'émettent pas encore
  d'événements (voir points ouverts).
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

## Bug découvert et corrigé pendant l'implémentation

`Site.content.isnot(None)` (utilisé par `dashboard.py` pour ne compter que les sites avec
du contenu généré) ne filtrait rien : SQLAlchemy stocke par défaut un `None` Python dans une
colonne `JSON` comme un littéral JSON `"null"`, **pas** un vrai `NULL` SQL — donc
`IS NOT NULL` ne l'excluait jamais. Corrigé à la racine dans `platform_core/models.py`
(`JSON(none_as_null=True)`), ce qui rend aussi ce comportement correct pour
`Post.content`/`Prospect.contact_message`, qui utilisent le même type partagé `_JSONB`.

## Points ouverts (pas encore fait, explicitement)

- Les agents Création de site, Réseaux sociaux et Maintenance n'émettent pas encore
  d'événements vers `ActivityEvent` — seul Prospection le fait. Le résumé transverse
  (`dashboard.py`) reste donc basé sur une lecture directe de leurs tables, pas sur le
  journal, pour l'instant cohérent mais à terme les deux mécanismes devront converger.
- Rappels de RDV automatiques (WhatsApp) — le module existe (`agents.prospection.whatsapp`)
  mais n'est pas branché sur les RDV.
- Synchronisation avec un vrai calendrier externe (Google Calendar) côté staff.
- Pas de compte staff individuel (même limite que `OPS_API_TOKEN` pour Maintenance) :
  `staff_contact` est un champ texte libre, pas une identité vérifiée.

## Rappel des permissions

- Autorisé : lire les données des 4 autres agents pour les agréger (jamais les modifier),
  journaliser ses propres événements, gérer les rendez-vous staff/client.
- Interdit : modifier le code ou les données propres d'un autre agent (CLAUDE.md §5), créer
  des événements au nom d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
