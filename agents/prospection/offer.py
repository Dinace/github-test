"""Génération d'un support visuel d'offre (PDF) pour un prospect, par pack."""

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from platform_core.models import Pack

_PACK_LABELS = {
    Pack.starter: "Starter",
    Pack.business: "Business",
    Pack.premium: "Premium",
}

# Résumé court par pack (CLAUDE.md §1, table des packs) — à ajuster si le détail des packs
# change, ce n'est pas une nouvelle source de vérité.
_DEFAULT_HIGHLIGHTS: dict[Pack, list[str]] = {
    Pack.starter: [
        "Un site vitrine professionnel, adapté à votre secteur",
        "Surveillance de disponibilité et sauvegardes régulières",
    ],
    Pack.business: [
        "Site complet + révisions illimitées",
        "Présence sur les réseaux sociaux (contenu, calendrier de publication)",
        "Prospection commerciale : fiches qualifiées chaque mois",
    ],
    Pack.premium: [
        "Site complet avec intégrations avancées",
        "Réseaux sociaux multi-plateformes + campagnes",
        "Prospection commerciale à grande échelle",
        "Support prioritaire",
    ],
}


def default_highlights_for_pack(pack: Pack) -> list[str]:
    return _DEFAULT_HIGHLIGHTS[pack]


def generate_offer_pdf(business_name: str, pack: Pack, highlights: list[str]) -> bytes:
    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    doc.setFont("Helvetica-Bold", 18)
    doc.drawString(2 * cm, height - 3 * cm, f"Offre de digitalisation — {business_name}")

    doc.setFont("Helvetica", 14)
    doc.drawString(2 * cm, height - 4.5 * cm, f"Pack proposé : {_PACK_LABELS[pack]}")

    doc.setFont("Helvetica", 11)
    y = height - 6 * cm
    for highlight in highlights:
        doc.drawString(2.3 * cm, y, f"• {highlight}")
        y -= 0.8 * cm

    doc.showPage()
    doc.save()
    return buffer.getvalue()
