import json
from subprocess import CompletedProcess

from agents.maintenance.security_scan import classify_urgency, run_pip_audit

_SAMPLE_OUTPUT = json.dumps(
    {
        "dependencies": [
            {
                "name": "example-package",
                "version": "1.0.0",
                "vulns": [
                    {"id": "GHSA-xxxx", "severity": "high", "description": "Vulnérabilité critique"},
                ],
            },
            {
                "name": "another-package",
                "version": "2.3.1",
                "vulns": [
                    {"id": "GHSA-yyyy", "severity": "low", "description": "Faible impact"},
                ],
            },
            {"name": "safe-package", "version": "3.0.0", "vulns": []},
        ]
    }
)


def _fake_run_command(*args, **kwargs) -> CompletedProcess:
    return CompletedProcess(args=args, returncode=0, stdout=_SAMPLE_OUTPUT, stderr="")


def test_run_pip_audit_parses_findings() -> None:
    findings = run_pip_audit(run_command=_fake_run_command)

    assert len(findings) == 2
    assert findings[0].package == "example-package"
    assert findings[0].severity == "high"


def test_run_pip_audit_handles_empty_output() -> None:
    def empty_run(*args, **kwargs) -> CompletedProcess:
        return CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    assert run_pip_audit(run_command=empty_run) == []


def test_classify_urgency_splits_by_severity() -> None:
    findings = run_pip_audit(run_command=_fake_run_command)

    urgent, deferred = classify_urgency(findings)

    assert len(urgent) == 1
    assert urgent[0].package == "example-package"
    assert len(deferred) == 1
    assert deferred[0].package == "another-package"
