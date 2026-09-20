from types import SimpleNamespace

import pytest

from agents.prospection.content import (
    ContentGenerationError,
    generate_contact_message,
    structure_prospect,
)


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **kwargs) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text)


def test_structure_prospect_parses_valid_response() -> None:
    payload = (
        '{"business_name": "Chez Awa", "sector": "restaurant", '
        '"likely_needs": "Un site vitrine et une présence sur les réseaux sociaux"}'
    )

    card = structure_prospect("Restaurant Chez Awa, Libreville, cuisine locale", client=_FakeClient(payload))

    assert card.business_name == "Chez Awa"
    assert card.sector == "restaurant"


def test_structure_prospect_raises_on_invalid_json() -> None:
    with pytest.raises(ContentGenerationError):
        structure_prospect("texte quelconque", client=_FakeClient("pas du JSON"))


def test_generate_contact_message_parses_valid_response() -> None:
    payload = '{"message": "Bonjour, nous accompagnons les commerces comme le vôtre..."}'

    result = generate_contact_message(
        "Chez Awa", "restaurant", "Site vitrine", "chaleureux", client=_FakeClient(payload)
    )

    assert "accompagnons" in result.message


def test_generate_contact_message_raises_on_schema_mismatch() -> None:
    with pytest.raises(ContentGenerationError):
        generate_contact_message(
            "Chez Awa", "restaurant", "Site vitrine", None, client=_FakeClient('{"unexpected": true}')
        )
