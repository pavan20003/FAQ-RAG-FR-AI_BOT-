"""Generate a coherent, entirely fictional French bakery corpus."""

from __future__ import annotations

import argparse
import html
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo_site"


@dataclass(frozen=True)
class Fact:
    key: str
    statement: str
    sources: tuple[str, ...]


FACTS = [
    Fact("address", "La boulangerie se trouve au 18 rue des Gras, 63000 Clermont-Ferrand.", ("contact.md", "access.md")),
    Fact("phone", "Le téléphone de la boutique est le 04 73 00 12 34.", ("contact.md",)),
    Fact("email", "L'adresse de contact est bonjour@trois-epis.example.", ("contact.md", "ordering.md")),
    Fact("hours_week", "Du mardi au vendredi, la boutique ouvre de 7 h à 19 h.", ("hours.md", "faq.md")),
    Fact("hours_sat", "Le samedi, la boutique ouvre de 7 h 30 à 18 h.", ("hours.md", "faq.md")),
    Fact("hours_sun", "Le dimanche, la boutique ouvre de 8 h à 12 h 30.", ("hours.md",)),
    Fact("closed", "La boutique est fermée le lundi.", ("hours.md", "faq.md")),
    Fact("baguette", "La baguette tradition (250 g) coûte 1,30 €.", ("breads.md", "prices.md", "products/baguette.md")),
    Fact("campagne", "Le pain de campagne (500 g) coûte 3,80 €.", ("breads.md", "prices.md")),
    Fact("seigle", "Le pain de seigle (400 g) coûte 4,20 €.", ("breads.md",)),
    Fact("complet", "Le pain complet (500 g) coûte 3,60 €.", ("breads.md", "allergens.md")),
    Fact("fougasse", "La fougasse aux olives coûte 4,50 € la pièce.", ("breads.md", "products/fougasse.md")),
    Fact("croissant", "Le croissant pur beurre coûte 1,20 €.", ("viennoiseries.md", "prices.md")),
    Fact("pain_choc", "Le pain au chocolat coûte 1,40 € depuis le 1er septembre 2026.", ("viennoiseries.md", "prices.md", "products/pain-au-chocolat.md")),
    Fact("brioche", "La brioche nature (400 g) coûte 6,50 €.", ("viennoiseries.md",)),
    Fact("chausson", "Le chausson aux pommes coûte 2,20 €.", ("viennoiseries.md",)),
    Fact("cookie", "Le cookie chocolat-noisette coûte 2,00 €.", ("pastries.md", "prices.md")),
    Fact("tarte", "La tarte aux pommes (6 parts) coûte 18 €.", ("pastries.md", "cakes.md")),
    Fact("cake_order", "Les gâteaux personnalisés sont à commander au moins 48 heures à l'avance.", ("cakes.md", "ordering.md")),
    Fact("cake_size", "Les gâteaux personnalisés sont proposés pour 6, 8 ou 10 personnes.", ("cakes.md",)),
    Fact("payment", "La boutique accepte les espèces, les cartes bancaires et les titres-restaurant papier.", ("payment.md", "faq.md")),
    Fact("zone1", "La livraison couvre Clermont-Ferrand intra-muros pour 5 € par commande.", ("delivery.md", "delivery_zones.md")),
    Fact("zone2", "Chamalières et Beaumont sont desservis pour 7 € par commande.", ("delivery.md", "delivery_zones.md")),
    Fact("zone3", "Aubière et Royat sont desservis pour 9 € par commande.", ("delivery_zones.md",)),
    Fact("free_delivery", "La livraison est offerte dès 45 € d'achat dans toutes les zones desservies.", ("delivery.md", "delivery_zones.md", "faq.md")),
    Fact("delivery_min", "Le montant minimum d'une commande livrée est de 15 € avant frais de livraison.", ("delivery.md", "ordering.md")),
    Fact("delivery_window", "Les créneaux de livraison sont de 8 h à 10 h et de 14 h à 17 h, du mardi au samedi.", ("delivery.md",)),
    Fact("delivery_cutoff", "Une commande en livraison doit être passée avant 16 h la veille.", ("delivery.md", "ordering.md")),
    Fact("pickup", "Le retrait en boutique est gratuit et se fait aux horaires d'ouverture.", ("ordering.md", "pickup.md")),
    Fact("custom_order", "Les commandes spéciales se réservent par téléphone ou par courriel.", ("ordering.md",)),
    Fact("wheat_allergen", "La baguette tradition, le pain de campagne et le pain complet contiennent du gluten (blé).", ("allergens.md", "breads.md")),
    Fact("dairy_allergen", "Le croissant et la brioche contiennent du lait.", ("allergens.md", "viennoiseries.md")),
    Fact("nuts_allergen", "Le cookie chocolat-noisette contient des noisettes.", ("allergens.md", "pastries.md")),
    Fact("cross_contact", "Les produits sont fabriqués dans un atelier qui manipule gluten, lait, œufs, fruits à coque et sésame; des traces croisées sont possibles.", ("allergens.md",)),
    Fact("returns", "Pour un produit non personnalisé, une réclamation est à signaler sous 14 jours après l'achat, avec le ticket.", ("returns.md", "faq.md")),
    Fact("perishable", "Les produits frais ou fabriqués sur commande ne sont ni repris ni échangés, sauf défaut constaté à la remise.", ("returns.md", "terms.md")),
    Fact("gift_card", "Les cartes cadeaux sont valables 12 mois à partir de leur date d'achat.", ("gift-cards.md", "faq.md")),
    Fact("gift_amount", "Une carte cadeau peut être chargée de 10 €, 25 € ou 50 €.", ("gift-cards.md",)),
    Fact("workshop", "Un atelier de façonnage du pain est proposé le premier samedi du mois, de 14 h à 16 h.", ("events.md",)),
    Fact("workshop_price", "L'atelier de façonnage coûte 35 € par personne et accueille 6 personnes au maximum.", ("events.md",)),
    Fact("seasonal", "La galette des rois est proposée en janvier, en format 4 parts à 12 € et 6 parts à 17 €.", ("seasonal.md",)),
    Fact("bread_storage", "Le pain se conserve idéalement dans un sac en papier, à température ambiante, et se congèle tranché.", ("storage.md",)),
    Fact("ingredients", "Les pains courants sont pétris sur place avec farine, eau, levain ou levure et sel; les recettes détaillées sont disponibles en boutique.", ("ingredients.md",)),
    Fact("sourcing", "La farine de blé des pains courants provient d'un moulin situé dans le Puy-de-Dôme.", ("sourcing.md",)),
    Fact("opening_order", "Les réservations de pains courants pour le lendemain sont acceptées jusqu'à 17 h par téléphone.", ("ordering.md",)),
    Fact("complaint", "Pour une réclamation, écrivez à bonjour@trois-epis.example en indiquant la date d'achat et le produit concerné.", ("returns.md", "contact.md")),
    Fact("access", "L'entrée de la boutique est de plain-pied; un arrêt de tram nommé Gaillard se trouve à environ 250 m.", ("access.md",)),
    Fact("community", "La boulangerie propose chaque mardi une miche de campagne à 3,50 € aux associations locales sur réservation.", ("community.md",)),
    Fact("privacy", "Les coordonnées communiquées pour une commande servent uniquement à son suivi et ne sont pas revendues.", ("privacy.md",)),
    Fact("cgv_payment", "Le paiement d'une commande spéciale est demandé au retrait; un acompte de 30 % est demandé pour les gâteaux personnalisés.", ("terms.md", "cakes.md")),
]


# Each page cites facts by stable key; the same registry supplies the fact ledger.
PAGES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("index.md", "Bienvenue chez Les Trois Épis", "Notre boulangerie artisanale fictive vous accueille à Clermont-Ferrand. Retrouvez ici les informations pratiques et les produits du jour.", ("address", "hours_week", "hours_sat", "hours_sun", "closed")),
    ("contact.md", "Contact", "Pour toute question ou commande, notre équipe vous répond pendant les horaires d'ouverture.", ("address", "phone", "email", "complaint")),
    ("hours.md", "Horaires", "Nos horaires habituels sont les suivants.", ("hours_week", "hours_sat", "hours_sun", "closed")),
    ("breads.md", "Pains", "Les poids indiqués correspondent aux formats vendus en boutique.", ("baguette", "campagne", "seigle", "complet", "fougasse", "wheat_allergen")),
    ("prices.md", "Tarifs", "Tarifs en vigueur depuis le 1er septembre 2026.", ("baguette", "campagne", "croissant", "pain_choc", "cookie", "tarte")),
    ("viennoiseries.md", "Viennoiseries", "Nos viennoiseries sont préparées sur place chaque matin.", ("croissant", "pain_choc", "brioche", "chausson", "dairy_allergen")),
    ("pastries.md", "Petites douceurs", "Une sélection de pâtisseries est disponible selon la production du jour.", ("cookie", "tarte", "nuts_allergen")),
    ("cakes.md", "Gâteaux et commandes personnalisées", "Les gâteaux personnalisés nécessitent une réservation anticipée.", ("cake_order", "cake_size", "cgv_payment", "tarte")),
    ("delivery.md", "Livraison", "Conditions actuellement applicables depuis le 1er septembre 2026.", ("zone1", "zone2", "free_delivery", "delivery_min", "delivery_window", "delivery_cutoff")),
    ("delivery_zones.md", "Zones et frais de livraison", "Les frais sont calculés par commande, quel que soit le nombre de colis.", ("zone1", "zone2", "zone3", "free_delivery")),
    ("ordering.md", "Commander", "Vous pouvez réserver en boutique, par téléphone ou par courriel.", ("delivery_min", "delivery_cutoff", "pickup", "custom_order", "opening_order")),
    ("pickup.md", "Retrait en boutique", "Le retrait permet de récupérer une commande sans frais de livraison.", ("pickup", "address", "opening_order")),
    ("allergens.md", "Allergènes", "Les informations ci-dessous concernent les recettes habituelles; demandez confirmation en boutique en cas d'allergie.", ("wheat_allergen", "dairy_allergen", "nuts_allergen", "cross_contact")),
    ("returns.md", "Réclamations et retours", "Politique en vigueur depuis le 1er septembre 2026.", ("returns", "perishable", "complaint")),
    ("gift-cards.md", "Cartes cadeaux", "Les cartes cadeaux sont disponibles à la caisse.", ("gift_card", "gift_amount")),
    ("events.md", "Ateliers", "Les places sont réservées dans l'ordre des demandes.", ("workshop", "workshop_price", "custom_order")),
    ("seasonal.md", "Produits de saison", "Les produits de saison sont disponibles dans la limite de la production.", ("seasonal",)),
    ("storage.md", "Conservation du pain", "Quelques gestes simples aident à garder votre pain plus longtemps.", ("bread_storage",)),
    ("ingredients.md", "Ingrédients", "Nous donnons ici les informations générales sur nos recettes de pains courants.", ("ingredients", "cross_contact")),
    ("sourcing.md", "Approvisionnement", "Nous privilégions un approvisionnement de proximité pour nos farines courantes.", ("sourcing",)),
    ("payment.md", "Moyens de paiement", "Règlement en boutique.", ("payment", "cgv_payment")),
    ("faq.md", "Questions fréquentes", "Quelques réponses rapides aux questions reçues le plus souvent.", ("hours_week", "closed", "baguette", "free_delivery", "returns", "gift_card", "payment")),
    ("about.md", "Notre atelier", "Les Trois Épis est une boulangerie artisanale imaginaire créée pour cette démonstration.", ("ingredients", "sourcing")),
    ("access.md", "Accès", "La boutique est située dans le centre de Clermont-Ferrand.", ("address", "access")),
    ("community.md", "Vie locale", "Nous réservons une offre hebdomadaire aux associations du quartier.", ("community", "phone")),
    ("privacy.md", "Confidentialité", "Nous limitons les informations conservées au suivi des commandes.", ("privacy", "email")),
    ("terms.md", "Conditions de vente", "Résumé des conditions applicables aux achats et commandes spéciales.", ("cgv_payment", "perishable", "returns", "custom_order")),
    ("products/baguette.md", "Baguette tradition", "Notre baguette tradition est cuite plusieurs fois par jour.", ("baguette", "wheat_allergen", "ingredients")),
    ("products/pain-au-chocolat.md", "Pain au chocolat", "Tarif en vigueur depuis le 1er septembre 2026.", ("pain_choc", "dairy_allergen")),
    ("products/fougasse.md", "Fougasse aux olives", "La fougasse est proposée selon la fournée du jour.", ("fougasse", "ingredients")),
]


PDFS = {
    "tarifs.pdf": (
        "Tarifs de la boutique",
        "Version en vigueur au 1er septembre 2026",
        ("baguette", "campagne", "croissant", "pain_choc", "cookie", "tarte"),
    ),
    "livraison.pdf": (
        "Conditions de livraison",
        "Version archivée du 1er mars 2026 — remplacée au 1er septembre 2026",
        ("zone1", "zone2", "free_delivery", "delivery_min", "delivery_window"),
    ),
    "retours.pdf": (
        "Politique de retour",
        "Version archivée du 1er mars 2026 — remplacée au 1er septembre 2026",
        ("perishable", "complaint"),
    ),
    "allergenes.pdf": (
        "Fiche allergènes",
        "Édition du 1er septembre 2026",
        ("wheat_allergen", "dairy_allergen", "nuts_allergen", "cross_contact"),
    ),
    "cgv.pdf": (
        "Conditions générales de vente",
        "Version archivée du 1er mars 2026 — remplacée au 1er septembre 2026",
        ("cgv_payment", "perishable", "returns"),
    ),
}

SUPERSEDED = [
    ("pain_choc", "Ancien prix : 1,30 € jusqu'au 31 août 2026; remplacé par le tarif en vigueur du 1er septembre 2026.", "tarifs.pdf"),
    ("zone1", "Ancien tarif Clermont-Ferrand : 4 € par commande jusqu'au 31 août 2026; remplacé par 5 € au 1er septembre 2026.", "livraison.pdf"),
    ("returns", "Ancien délai de réclamation : 7 jours après achat jusqu'au 31 août 2026; remplacé par 14 jours au 1er septembre 2026.", "retours.pdf"),
]


def fact_map() -> dict[str, Fact]:
    return {fact.key: fact for fact in FACTS}


def _write_pdf_reportlab(path: Path, title: str, version: str, lines: list[str]) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    story = [Paragraph(html.escape(title), styles["Title"]), Paragraph(html.escape(version), styles["Normal"]), Spacer(1, 8 * mm)]
    story.extend(Paragraph(html.escape(line), styles["BodyText"]) for line in lines)
    SimpleDocTemplate(str(path), pagesize=A4, title=title).build(story)


def _write_pdf_fallback(path: Path, title: str, version: str, lines: list[str]) -> None:
    """Write a small valid PDF using built-in fonts when ReportLab is unavailable."""
    paragraphs = [title, version, "", *lines]
    wrapped = [part for paragraph in paragraphs for part in textwrap.wrap(paragraph, 88) or [""]]
    pages = [wrapped[index : index + 44] for index in range(0, len(wrapped), 44)]
    objects: list[bytes] = []
    page_ids: list[int] = []

    def add(value: bytes) -> int:
        objects.append(value)
        return len(objects)

    catalog_id = add(b"")
    pages_id = add(b"")
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for page_lines in pages:
        text_ops = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        for line in page_lines:
            # WinAnsiEncoding covers the French accents used in this corpus.
            encoded = line.encode("cp1252", errors="replace")
            escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
            text_ops.append("(" + escaped.decode("latin-1") + ") Tj T*" )
        text_ops.append("ET")
        stream = "\n".join(text_ops).encode("latin-1")
        content_id = add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        page_id = add(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode()
        )
        page_ids.append(page_id)
    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, content in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + content + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    path.write_bytes(output)


def generate() -> None:
    by_key = fact_map()
    if len(by_key) != len(FACTS):
        raise ValueError("Fact keys must be unique")
    for _, _, _, keys in PAGES:
        missing = set(keys) - by_key.keys()
        if missing:
            raise ValueError(f"Unknown fact keys: {sorted(missing)}")
    known_sources = {relative for relative, _, _, _ in PAGES} | set(PDFS)
    for fact in FACTS:
        missing = set(fact.sources) - known_sources
        if missing:
            raise ValueError(f"Unknown source paths for {fact.key}: {sorted(missing)}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source_root = ROOT / "data"
    source_root.mkdir(parents=True, exist_ok=True)
    for relative, title, intro, keys in PAGES:
        destination = DATA_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# {title}", "", intro, "", *[f"- {by_key[key].statement}" for key in keys], ""]
        destination.write_text("\n".join(lines), encoding="utf-8")

    for filename, (title, version, keys) in PDFS.items():
        lines = [by_key[key].statement for key in keys]
        for key, statement, source in SUPERSEDED:
            if source == filename:
                lines.append(statement)
        path = DATA_DIR / filename
        try:
            _write_pdf_reportlab(path, title, version, lines)
        except ImportError:
            _write_pdf_fallback(path, title, version, lines)

    page_sources: dict[str, set[str]] = {fact.key: set(fact.sources) for fact in FACTS}
    for relative, _, _, keys in PAGES:
        for key in keys:
            page_sources[key].add(relative)
    for filename, (_, _, keys) in PDFS.items():
        for key in keys:
            page_sources[key].add(filename)
    fact_rows = [
        "# Demo corpus fact ledger", "",
        "All businesses and products below are fictional. Current facts are written in the Markdown pages and, where applicable, the PDFs. The three archived PDFs below deliberately preserve older statements; each is clearly marked as superseded.", "",
        "## Current facts", "",
        "| Fact | Statement | Source files |", "|---|---|---|",
    ]
    for fact in FACTS:
        sources = sorted(page_sources[fact.key])
        fact_rows.append(f"| `{fact.key}` | {fact.statement} | {', '.join(f'`demo_site/{source}`' for source in sources)} |")
    fact_rows.extend(["", "## Deliberate superseded versions", "", "| Fact | Older statement | Archived source | Current source |", "|---|---|---|---|"])
    for key, older_statement, source in SUPERSEDED:
        current_sources = sorted(page_sources[key] - {source})
        fact_rows.append(f"| `{key}` | {older_statement} | `demo_site/{source}` | {', '.join(f'`demo_site/{current}`' for current in current_sources)} |")
    (source_root / "FACTS.md").write_text("\n".join(fact_rows) + "\n", encoding="utf-8")
    print(f"Generated {len(PAGES)} pages, {len(PDFS)} PDFs and {len(FACTS)} current facts in {DATA_DIR}")


def verify() -> None:
    pages = sorted(DATA_DIR.rglob("*.md"))
    pdfs = sorted(DATA_DIR.rglob("*.pdf"))
    if len(pages) != len(PAGES) or len(pdfs) != len(PDFS):
        raise SystemExit(f"Expected {len(PAGES)} Markdown pages and {len(PDFS)} PDFs; found {len(pages)} and {len(pdfs)}")
    for pdf in pdfs:
        if not pdf.read_bytes().startswith(b"%PDF-"):
            raise SystemExit(f"Invalid PDF header: {pdf}")
    ledger = (ROOT / "data" / "FACTS.md").read_text(encoding="utf-8")
    if ledger.count("| `") < len(FACTS) + len(SUPERSEDED):
        raise SystemExit("Fact ledger is missing entries")
    print(f"Verified {len(pages)} Markdown pages, {len(pdfs)} PDFs and fact ledger")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="check generated file counts and PDF headers")
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        generate()
