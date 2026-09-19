# Modèle de coût unitaire par pack

Objectif : vérifier si les quotas chiffrés des 3 packs (CLAUDE.md §1) sont financièrement
tenables. Document de travail, à réviser avec des données d'usage réelles une fois l'app en
production (voir section "Ce qui reste inconnu").

## Tarifs connus (au 2026-09-19)

**API Claude** (tarifs officiels par million de tokens) :

| Modèle | Input | Output |
|---|---|---|
| Claude Sonnet 5 | 2,00 $ | 10,00 $ |
| Claude Haiku 4.5 | 1,00 $ | 5,00 $ |

**Cloudflare R2** : stockage ~0,015 $/Go/mois, pas de frais de sortie (egress). Coût
négligeable pour des sites statiques légers et des dumps PostgreSQL compressés.

**Fly.io** : coût d'infrastructure partagé (app + PostgreSQL), pas un coût marginal par
client à faible volume — à revisiter une fois le nombre de clients connu.

## Estimation du coût Claude API par action d'agent

Hypothèses de volumétrie de tokens par action (estimations de travail — à corriger avec des
mesures réelles `response.usage` une fois l'app en production, comme le recommande le
process standard d'optimisation de coûts API). Modèle utilisé par défaut : **Haiku 4.5**
pour les tâches de génération courtes/répétitives (posts, fiches prospect), **Sonnet 5**
pour les tâches nécessitant plus de qualité rédactionnelle (contenu de site, supports
d'offre) — choix de coût, à réévaluer si la qualité observée est insuffisante en pratique.

| Action | Modèle | Tokens (in/out, estimés) | Coût estimé |
|---|---|---|---|
| Génération complète d'un site | Sonnet 5 | 3 000 / 4 000 | ~0,05 $ |
| Révision de site | Sonnet 5 | 1 500 / 1 500 | ~0,02 $ |
| Post réseaux sociaux (texte + légende) | Haiku 4.5 | 500 / 300 | ~0,002 $ |
| Fiche prospect (extraction + structuration) | Haiku 4.5 | 1 000 / 500 | ~0,0035 $ |
| Support visuel d'offre (contenu texte) | Sonnet 5 | 800 / 600 | ~0,008 $ |

## Coût Claude API mensuel estimé par pack

En reprenant les quotas définis dans CLAUDE.md §1 (hypothèse d'usage moyen, pas le
plafond du quota pour les éléments "illimités") :

| | Starter | Business | Premium |
|---|---|---|---|
| Site (génération + révisions) | 1 génération + 2 révisions ≈ 0,09 $ | 1 génération + 4 révisions ≈ 0,13 $ | 1 génération + 8 révisions ≈ 0,21 $ |
| Réseaux sociaux (posts) | — | 12 posts ≈ 0,05 $ | 30 posts ≈ 0,12 $ |
| Prospection (fiches + supports) | — | 20 fiches + 1 support ≈ 0,15 $ | 60 fiches + 5 supports ≈ 0,46 $ |
| **Total Claude API estimé** | **≈ 0,09 $/mois** | **≈ 0,33 $/mois** | **≈ 0,79 $/mois** |

## Conclusion

**Le coût de l'API Claude n'est pas le facteur limitant** pour la viabilité des packs —
même pour Premium, il reste sous 1 $/mois/client, très en dessous de tout prix
d'abonnement plausible pour ce marché. **Les quotas définis dans CLAUDE.md §1 sont donc
validés du point de vue du coût Claude API.**

Les vrais leviers de coût à surveiller sont ailleurs :
- **WhatsApp Business API**, **Google Places API**, **paiement mobile money** : voir données
  de marché ci-dessous (recherche web, 2026-09-19) — partiellement chiffrables, un devis
  direct reste nécessaire pour les montants précis au Gabon.
- **Infrastructure** (Fly.io, R2) : coût partagé entre tous les clients, pas un coût
  marginal linéaire par client à ce stade — à revisiter une fois un volume de clients réel
  connu.
- **Temps humain** (support, onboarding, validation des contenus sensibles) : coût réel non
  capturé par ce modèle, à budgéter séparément.

## Données de marché (recherche web, 2026-09-19)

**WhatsApp Business API** — le modèle a changé depuis juillet 2025 : ce n'est plus une
tarification "à la conversation" mais **au message envoyé** (catégories marketing/utility/
authentication), tarif dépendant du **pays du destinataire** (pas de l'expéditeur). Exemples
trouvés : Inde ~0,009 $/message, Brésil ~0,063 $, US ~0,025 $, UAE ~0,050 $ — aucun tarif
Gabon publié publiquement par Meta. À cela s'ajoute une marge de la plateforme d'envoi (BSP,
"Business Solution Provider") de l'ordre de 0,003–0,010 $/message. **Action requise** :
obtenir un devis direct d'un BSP couvrant le Gabon avant de fixer le prix final des packs
Business/Premium (le calcul devra être refait poste "au message", pas "à la conversation"
comme supposé initialement dans les sections Réseaux sociaux/Prospection des `skills/
README.md`).

**Google Places API** (Place Details, pertinent pour l'agent Prospection) : environ
17–20 $/1000 requêtes pour les champs de base, jusqu'à 35–40 $/1000 avec avis et horaires
d'ouverture inclus. Un quota gratuit mensuel existe (de l'ordre de 1000 requêtes/mois en
tier Enterprise). Estimation d'impact sur le pack Premium (60 fiches/mois) : entre ~1,20 $
et ~2,40 $/mois/client selon les champs demandés — plus significatif que le coût Claude API
mais reste modeste. À confirmer une fois le champ de données exact nécessaire par fiche
prospect précisé.

**Paiement mobile money au Gabon** :
- **Airtel Money** (≈40% des comptes mobile money au Gabon) : intégration marchande
  (Collections API + webhook) facturée **350 000 à 600 000 FCFA en coût d'intégration
  ponctuel** (délai 3 à 5 jours, principalement lié à la validation KYC du compte marchand),
  puis **environ 2% de commission sur le volume collecté**. Donnée concrète à intégrer au
  business plan (coût fixe de mise en route + coût variable récurrent sur les encaissements).
- **Moov Money** : un produit marchand ("Moov Money Online") existe et un SDK tiers (PHP)
  est documenté publiquement, mais aucune grille de frais/commission n'a été trouvée
  publiquement — nécessite un contact direct avec Moov Money Gabon pour obtenir les
  conditions marchandes.
- **Orange Money** : non re-vérifié dans cette recherche, à confirmer de la même manière.

Sources : [WhatsApp Business API Pricing 2026 (Blueticks)](https://blueticks.co/blog/whatsapp-business-api-pricing-2026), [Pricing on the WhatsApp Business Platform (Meta for Developers)](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing), [Google Places API Pricing 2026 (Woosmap)](https://www.woosmap.com/blog/google-places-api-pricing), [Places API Usage and Billing (Google for Developers)](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing), [Intégrer Airtel Money site web Gabon (Kolonell)](https://kolonell.com/fr/blog/integrer-airtel-money-site-web-gabon-libreville-2026), [Services Marchands Moov Money Gabon](https://moovmoney.ga/services/services-marchands/).

## Cadre de réflexion pour le prix d'abonnement (pas un prix final)

**Ce que je peux établir : le plancher de coût variable.** En combinant le coût Claude API,
une estimation Google Places (Prospection) et une allocation modeste WhatsApp/infrastructure
(taux indicatif ~610 FCFA/$) :

| | Starter | Business | Premium |
|---|---|---|---|
| Plancher de coût variable estimé | ~600–1 200 FCFA/mois | ~1 800–3 600 FCFA/mois | ~3 600–6 700 FCFA/mois |

À cela s'ajoute, une fois le prix fixé, ~2% de commission mobile money **sur le prix
lui-même** (proportionnel, pas un montant fixe).

**Ce que je ne peux pas établir : la disposition à payer réelle des PME/indépendants
gabonais pour un abonnement récurrent.** Ce n'est pas une donnée qu'une recherche web permet
de connaître de façon fiable — elle dépend du terrain (entretiens clients, test de prix,
veille concurrentielle locale sur les agences web/community managers/prospecteurs
freelances). Je ne vais pas inventer un chiffre "validé" ici.

**Ancrage de valeur utilisable pour la discussion** : l'argument de vente n'est pas "moins
cher que le coût de la plateforme" (déjà acquis, marge très confortable sur ce plan) mais
"moins cher, en continu, que cumuler un développeur freelance (site, souvent facturé au
forfait one-shot), un community manager freelance (forfait mensuel) et un commercial de
prospection (salaire)" — la comparaison pertinente est contre ces alternatives locales, pas
contre le coût interne de la plateforme.

**Recommandation méthodologique** : ne pas figer un prix définitif sans test terrain. Fixer
une fourchette hypothèse, la confronter à un petit nombre de prospects réels (entretiens ou
test de prix type Van Westendorp), et ajuster avant un lancement à grande échelle. Exemple
de fourchette de travail pour amorcer ce test (non validée, à ajuster) :

| | Starter | Business | Premium |
|---|---|---|---|
| Fourchette hypothèse à tester | 8 000–15 000 FCFA/mois | 20 000–35 000 FCFA/mois | 40 000–70 000 FCFA/mois |

Ces montants donnent une marge confortable au-dessus du plancher de coût variable estimé
ci-dessus, mais **restent une hypothèse de travail à valider sur le terrain**, pas un prix
décidé.

## Ce qui reste inconnu (pas une décision technique, nécessite un devis/contact direct)

- Tarif WhatsApp Business par message pour les destinataires au Gabon (devis BSP).
- Grille de commission Moov Money Gabon (contact direct nécessaire) et reconfirmation de
  celle d'Orange Money.
- Prix d'abonnement final par pack (en FCFA) — décision commerciale, pas technique.
- Mesure réelle des tokens consommés par action une fois l'app en production (ces
  estimations doivent être recalibrées avec `response.usage` réel, pas seulement supposées).
- Budget d'intégration paiement à prévoir dès le lancement : ~350–600k FCFA pour Airtel
  Money seul, montant équivalent probable pour Moov Money une fois ses conditions connues.
