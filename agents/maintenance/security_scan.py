"""Scan de sécurité basique des dépendances Python via pip-audit.

Note d'honnêteté : le schéma JSON exact de `pip-audit --format=json` et la disponibilité
d'un champ de sévérité par vulnérabilité n'ont pas été vérifiés contre la documentation
officielle à jour dans cette session (pas de connexion vérifiée à l'outil réel). Le parsing
ci-dessous suit le schéma documenté au moment de l'écriture (liste `dependencies`, chacune
avec `vulns`) mais reste à valider contre une exécution réelle de `pip-audit` avant mise en
production — les champs manquants sont traités avec des valeurs de repli plutôt que de
lever une exception.
"""

import json
import subprocess
from collections.abc import Callable

from pydantic import BaseModel

_HIGH_URGENCY_SEVERITIES = {"high", "critical"}


class SecurityFinding(BaseModel):
    package: str
    installed_version: str
    vulnerability_id: str
    severity: str = "unknown"
    description: str = ""


def run_pip_audit(*, run_command: Callable[..., subprocess.CompletedProcess] | None = None) -> list[SecurityFinding]:
    run_command = run_command or subprocess.run
    result = run_command(["pip-audit", "--format=json"], capture_output=True, text=True, check=False)

    if not result.stdout.strip():
        return []

    payload = json.loads(result.stdout)
    findings: list[SecurityFinding] = []
    for dependency in payload.get("dependencies", []):
        for vuln in dependency.get("vulns", []):
            severity = vuln.get("severity")
            findings.append(
                SecurityFinding(
                    package=dependency.get("name", "inconnu"),
                    installed_version=dependency.get("version", "inconnue"),
                    vulnerability_id=vuln.get("id", "inconnu"),
                    severity=severity.lower() if severity else "unknown",
                    description=vuln.get("description", ""),
                )
            )
    return findings


def classify_urgency(findings: list[SecurityFinding]) -> tuple[list[SecurityFinding], list[SecurityFinding]]:
    """Retourne (findings_urgents, findings_résumé_hebdo) selon le seuil de sévérité
    (agents/maintenance/skills/README.md) : haute/critique = notification immédiate,
    faible/moyenne (ou inconnue) = résumé hebdomadaire."""
    urgent = [f for f in findings if f.severity in _HIGH_URGENCY_SEVERITIES]
    deferred = [f for f in findings if f.severity not in _HIGH_URGENCY_SEVERITIES]
    return urgent, deferred
