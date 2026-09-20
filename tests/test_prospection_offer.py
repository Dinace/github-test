from agents.prospection.offer import default_highlights_for_pack, generate_offer_pdf
from platform_core.models import Pack


def test_generate_offer_pdf_returns_valid_pdf_bytes() -> None:
    pdf_bytes = generate_offer_pdf("Chez Awa", Pack.business, ["Site vitrine", "Réseaux sociaux"])

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


def test_default_highlights_differ_by_pack() -> None:
    assert default_highlights_for_pack(Pack.starter) != default_highlights_for_pack(Pack.premium)
