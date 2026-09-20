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

Les moyens de paiement disponibles dépendent du pays. Au lancement (Gabon), les opérateurs
mobile money pertinents sont Orange Money, Airtel Money et Moov Money — **MTN n'opère pas au
Gabon** et Wave n'y est pas confirmé, ces deux clés sont conservées pour l'extension vers
d'autres pays où ils opèrent (Afrique de l'Ouest notamment). Voir CLAUDE.md §1
"Scalabilité multi-pays" : le choix des moyens de paiement actifs doit être paramétrable par
pays, pas figé pour toute la plateforme.

| Variable | Service | Utilisée par | Usage |
|---|---|---|---|
| `ORANGE_MONEY_API_KEY` | Orange Money | Plateforme (facturation) | Paiements/abonnements clients. Actif au Gabon. Aucun agent métier n'a le droit d'initier un paiement réel sans validation humaine (voir CLAUDE.md §5). |
| `AIRTEL_MONEY_API_KEY` | Airtel Money | Plateforme (facturation) | Idem Orange Money. Actif au Gabon. |
| `MOOV_MONEY_API_KEY` | Moov Money | Plateforme (facturation) | Idem Orange Money. Actif au Gabon. |
| `MTN_MOMO_API_KEY` | MTN Mobile Money | Plateforme (facturation) | Idem Orange Money. **Réservé** : MTN n'opère pas au Gabon, à activer lors de l'extension vers un pays où MTN est présent. |
| `WAVE_API_KEY` | Wave | Plateforme (facturation) | Idem Orange Money. **Réservé** : présence non confirmée au Gabon, à activer lors de l'extension (Wave est surtout présent en Afrique de l'Ouest). |
| `META_ADS_TOKEN` | Meta Ads (Facebook/Instagram) | Agent Réseaux sociaux | Publication de contenu et gestion de campagnes, sur validation préalable uniquement. |
| `META_APP_ID` / `META_APP_SECRET` | Meta for Developers | Agent Réseaux sociaux | Authentification applicative aux API Meta. |
| `WHATSAPP_BUSINESS_TOKEN` | WhatsApp Business API | Agent Réseaux sociaux, Agent Prospection (notifications) | Envoi de messages/notifications côté client, jamais de démarchage de prospects filtrés "non favorable"/"non joignable". |
| `GOOGLE_ADS_TOKEN` | Google Ads | Agent Réseaux sociaux | Campagnes publicitaires, sur validation préalable uniquement. |
| `GOOGLE_BUSINESS_PROFILE_TOKEN` | Google Business Profile | Agent Réseaux sociaux, Agent Création de site | Fiche établissement du client, référencement local. |
| `DATABASE_URL` | PostgreSQL managé (Fly Postgres) | Plateforme (tous les agents, via la couche d'accès aux données) | Connexion à la base de données. |
| `SENTRY_DSN` | Sentry (ou équivalent) | Agent Maintenance | Détection et remontée d'anomalies/bugs. |
| `UPTIME_MONITOR_TOKEN` | Service de monitoring (ex. UptimeRobot) | Agent Maintenance | Surveillance de disponibilité des sites clients. |
| `OPS_API_TOKEN` | Interne (pas un service tiers) | Agent Maintenance (`app/routers/maintenance.py`) | Jeton partagé pour les endpoints internes staff (notifications, backups, restauration). **Stopgap explicite** : pas un vrai système d'auth staff (comptes individuels, rôles) — voir `platform_core/config.py`. |
| `FLY_API_TOKEN` | Fly.io | Infrastructure (déploiement/CI-CD) | Déploiement de l'app et de la base ; non consommée par un agent métier à l'exécution. |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare | Agent Création de site, Agent Maintenance | Identifiant de compte Cloudflare (R2 + CDN). |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` / `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | Cloudflare R2 | Agent Création de site, Agent Maintenance | Stockage/diffusion des sites clients générés et des sauvegardes. |
| `CLOUDFLARE_R2_BUCKET` | Cloudflare R2 | Agent Création de site, Agent Maintenance | Nom du bucket R2 utilisé. |

Cette liste sera complétée au fil du projet (ex. clé de génération d'images, etc.) — toute
nouvelle clé doit être ajoutée ici et dans `.env.example` avant d'être utilisée par un
agent, avec une entrée correspondante dans `MEMORY.md`.
