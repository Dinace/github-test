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
| **Claude Agent SDK — génération de contenu** | Rédaction des textes de publication (posts, légendes, réponses type) adaptés au ton/secteur du client, à partir du brief. | Cohérent avec l'orchestration globale du projet ; permet de conditionner la génération à un brief structuré et de conserver la trace de ce qui a été généré/validé. |
| **Meta Graph API** (`META_ADS_TOKEN`, `META_APP_ID/SECRET`) | Publication et gestion de campagnes sur Facebook/Instagram. | API officielle, seule voie légitime pour publier au nom du client ; nécessaire pour respecter les conditions d'utilisation des plateformes. |
| **WhatsApp Business API** (`WHATSAPP_BUSINESS_TOKEN`) | Messages clients (confirmations, notifications), catalogue produit si applicable. | Canal de communication le plus utilisé par les PME/indépendants dans le marché cible ; API officielle obligatoire pour un usage professionnel conforme. |
| **APScheduler / Celery beat** | Planification du calendrier de publication (dates/heures programmées). | Solution standard en Python pour des tâches planifiées ; Celery beat si l'infrastructure prévoit déjà une file de tâches (ex. pour la Maintenance), sinon APScheduler pour un besoin plus léger. |
| **Pillow** (+ gabarits graphiques) | Génération de visuels simples (bannières, citations, promos) à partir d'un template de marque par client. | Suffisant pour des visuels basiques sans dépendance à un service tiers payant ; à réévaluer si un besoin de design plus avancé émerge (ex. API Canva). |

## Points à trancher avant implémentation

- Format exact du "brief/validation préalable" requis avant toute publication (qui valide,
  où, avec quelle traçabilité dans `MEMORY.md`/base de données).
- Portée initiale : Meta + WhatsApp Business en priorité ; Google Business Profile et
  Google Ads déjà prévus dans `config/credentials/README.md` mais à confirmer pour le MVP.
- Solution de génération de visuels plus avancée si Pillow s'avère insuffisant.

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : générer du contenu à partir d'un brief, planifier des publications, publier
  **uniquement** si un brief ou une validation existe pour ce contenu précis.
- Interdit : publier sans validation préalable, modifier le code/les données d'un autre
  agent, utiliser une clé API en dehors de `config/credentials/`.
