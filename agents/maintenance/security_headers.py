"""Audit des en-têtes de sécurité HTTP d'un site.

Comble une partie du point ouvert "scan de sécurité des sites clients générés eux-mêmes
(en-têtes HTTP)" — seule la moitié utile aujourd'hui : la logique d'audit elle-même est
indépendante de la question non tranchée de l'URL publique d'un site généré par la
plateforme (`Site` n'a pas de champ URL, voir MEMORY.md et agents/maintenance/skills/
README.md, "points ouverts"). Cette fonction prend une URL en **paramètre explicite**,
elle ne la déduit jamais d'un `Site` — utilisable dès maintenant en déclenchement manuel
(`POST /api/maintenance/security-scan/headers`, staff) sur n'importe quelle URL, y compris
le site d'un client externe. Le jour où un schéma d'URL publique existe pour les sites
générés, brancher un équivalent planifié de `run_security_scans` dessus est immédiat.
"""

import httpx
from pydantic import BaseModel

_HIGH_URGENCY_SEVERITIES = {"high"}

# En-têtes de sécurité HTTP standards — sévérité et recommandation courtes, dans le même
# esprit que security_scan.py (pip-audit) : un premier niveau de contrôle, pas un audit
# exhaustif (type Mozilla Observatory).
_EXPECTED_HEADERS: list[tuple[str, str, str]] = [
    (
        "Strict-Transport-Security",
        "high",
        "Force HTTPS pour tous les visiteurs et empêche le downgrade vers HTTP.",
    ),
    (
        "X-Content-Type-Options",
        "medium",
        "Empêche le navigateur de deviner un type MIME différent de celui déclaré.",
    ),
    (
        "X-Frame-Options",
        "medium",
        "Empêche l'intégration du site dans une iframe tierce (protection contre le clickjacking).",
    ),
    (
        "Content-Security-Policy",
        "medium",
        "Restreint les sources de scripts/styles chargées, réduit l'impact d'une injection XSS.",
    ),
    (
        "Referrer-Policy",
        "low",
        "Limite les informations envoyées dans l'en-tête Referer vers des sites tiers.",
    ),
]


class SecurityHeaderFinding(BaseModel):
    header: str
    present: bool
    severity: str
    recommendation: str


def check_security_headers(
    url: str, *, http_client: httpx.Client | None = None, timeout: float = 5.0
) -> list[SecurityHeaderFinding]:
    client = http_client or httpx.Client()
    response = client.get(url, timeout=timeout, follow_redirects=True)

    findings = []
    for header_name, severity, recommendation in _EXPECTED_HEADERS:
        findings.append(
            SecurityHeaderFinding(
                header=header_name,
                present=header_name in response.headers,
                severity=severity,
                recommendation=recommendation,
            )
        )
    return findings


def classify_urgency(
    findings: list[SecurityHeaderFinding],
) -> tuple[list[SecurityHeaderFinding], list[SecurityHeaderFinding]]:
    """Retourne (findings_urgents, findings_résumé_hebdo) parmi les en-têtes **manquants**
    uniquement — même seuil de sévérité que `security_scan.py::classify_urgency`
    (agents/maintenance/skills/README.md) : haute = notification immédiate, moyenne/faible
    = résumé hebdomadaire. Un en-tête présent n'est jamais un "finding"."""
    missing = [f for f in findings if not f.present]
    urgent = [f for f in missing if f.severity in _HIGH_URGENCY_SEVERITIES]
    deferred = [f for f in missing if f.severity not in _HIGH_URGENCY_SEVERITIES]
    return urgent, deferred
