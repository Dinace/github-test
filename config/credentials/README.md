# Clés et identifiants — config/credentials/

Ce dossier centralise la **liste** des clés/tokens utilisés par les agents de la
plateforme. Il ne contient **jamais de valeur réelle** : uniquement le nom des variables
attendues, leur usage, et l'agent qui les consomme.

- `.env.example` : gabarit versionné, valeurs vides — à copier vers `.env`.
- `.env` : fichier réel, **non versionné** (voir `.gitignore`), rempli manuellement par
  l'équipe projet. Aucun agent IA ne doit créer, modifier ou lire le contenu de ce fichier
  au-delà des noms de variables qu'il déclare.

## Règle absolue : la clé API Claude

La clé API Claude/Anthropic **n'est jamais stockée ici**, ni dans aucun fichier du dépôt.
Elle est gérée séparément par l'équipe projet (variable d'environnement d'exécution /
secret manager de la plateforme d'hébergement). Aucun agent n'a le droit de la lire, la
transmettre ou la journaliser.

## Liste des clés attendues par agent

| Variable | Service | Utilisée par | Usage |
|---|---|---|---|
| `ORANGE_MONEY_API_KEY` | Orange Money | Plateforme (facturation) | Paiements/abonnements clients. Aucun agent métier n'a le droit d'initier un paiement réel sans validation humaine (voir CLAUDE.md §5). |
| `MTN_MOMO_API_KEY` | MTN Mobile Money | Plateforme (facturation) | Idem Orange Money. |
| `WAVE_API_KEY` | Wave | Plateforme (facturation) | Idem Orange Money. |
| `META_ADS_TOKEN` | Meta Ads (Facebook/Instagram) | Agent Réseaux sociaux | Publication de contenu et gestion de campagnes, sur validation préalable uniquement. |
| `META_APP_ID` / `META_APP_SECRET` | Meta for Developers | Agent Réseaux sociaux | Authentification applicative aux API Meta. |
| `WHATSAPP_BUSINESS_TOKEN` | WhatsApp Business API | Agent Réseaux sociaux, Agent Prospection (notifications) | Envoi de messages/notifications côté client, jamais de démarchage de prospects filtrés "non favorable"/"non joignable". |
| `GOOGLE_ADS_TOKEN` | Google Ads | Agent Réseaux sociaux | Campagnes publicitaires, sur validation préalable uniquement. |
| `GOOGLE_BUSINESS_PROFILE_TOKEN` | Google Business Profile | Agent Réseaux sociaux, Agent Création de site | Fiche établissement du client, référencement local. |
| `DATABASE_URL` | PostgreSQL | Plateforme (tous les agents, via la couche d'accès aux données) | Connexion à la base de données. |
| `SENTRY_DSN` | Sentry (ou équivalent) | Agent Maintenance | Détection et remontée d'anomalies/bugs. |
| `UPTIME_MONITOR_TOKEN` | Service de monitoring (ex. UptimeRobot) | Agent Maintenance | Surveillance de disponibilité des sites clients. |
| `BACKUP_STORAGE_KEY` | Stockage objet (backups) | Agent Maintenance | Sauvegardes des sites/données clients. |

Cette liste sera complétée au fil du projet (ex. clé de génération d'images, service
d'hébergement des sites générés, etc.) — toute nouvelle clé doit être ajoutée ici et dans
`.env.example` avant d'être utilisée par un agent, avec une entrée correspondante dans
`MEMORY.md`.
