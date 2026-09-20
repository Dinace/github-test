from types import SimpleNamespace

from agents.planning.dashboard import ClientActivitySummary
from agents.planning.digest import generate_digest


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **kwargs) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text)


def test_generate_digest_returns_claude_text() -> None:
    summary = ClientActivitySummary(
        sites_awaiting_validation=1,
        posts_awaiting_validation=2,
        prospects_to_qualify=3,
        prospects_awaiting_contact_validation=0,
    )

    digest = generate_digest(summary, client=_FakeClient("Ce client a plusieurs éléments en attente de validation."))

    assert "en attente" in digest
