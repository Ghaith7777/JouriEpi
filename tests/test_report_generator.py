"""DOCX dossier generation and provenance checks."""

from io import BytesIO

import pytest
from docx import Document

from core.engine_2x2 import Table2x2, analyze_2x2
from core.report_generator import generate_clinical_dossier
from ui.components import forest_plot_png_bytes


def test_generates_readable_word_dossier_with_methods_metadata_hash_and_figure():
    counts = (25, 15, 7, 30)
    result = analyze_2x2(Table2x2(*counts))
    png = forest_plot_png_bytes(result)
    payload = generate_clinical_dossier(
        counts, result, design="Cohort / cross-sectional",
        title="Respiratory outcomes study",
        metadata_fields={"Study ID": "TEST-001", "Setting": "Example clinic"},
        forest_png=png,
    )
    assert payload[:2] == b"PK"
    document = Document(BytesIO(payload))
    text = "\n".join(p.text for p in document.paragraphs)
    assert "JOURIEPI" in text
    assert "Statistical methods & algorithmic provenance" in text
    assert "Katz" in text and "Woolf" in text and "Wilson" in text and "Boschloo" in text
    assert "Respiratory outcomes study" in text
    assert "SHA-256" in text
    assert "does not, by itself, satisfy FDA 21 CFR Part 11" in text
    assert len(document.tables) >= 3
    assert len(document.inline_shapes) == 1


def test_dossier_includes_evalue_and_stratification_when_provided():
    from core.causal_sensitivity import e_value
    from core.stratification import analyze_stratified_tables

    result = analyze_2x2(Table2x2(20, 10, 10, 20))
    strata = analyze_stratified_tables({"young": (12, 8, 6, 14), "older": (20, 10, 10, 20)})
    ev = e_value(2.0, (1.2, 3.0))
    document = Document(BytesIO(generate_clinical_dossier(
        (20, 10, 10, 20), result, stratified_result=strata, e_value_result=ev)))
    text = "\n".join(p.text for p in document.paragraphs)
    assert "E-value" in text
    assert "Simpson's paradox reversal flag" in text
    assert any("Stratum-specific estimates" in p.text for p in document.paragraphs)


def test_institutional_logo_is_embedded_in_repeating_word_header():
    from PIL import Image

    image = Image.new("RGB", (48, 24), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    counts = (25, 15, 7, 30)
    result = analyze_2x2(Table2x2(*counts))
    document = Document(BytesIO(generate_clinical_dossier(counts, result, logo_bytes=buffer.getvalue())))
    assert sum(1 for rel in document.sections[0].header.part.rels.values() if rel.reltype.endswith("/image")) == 1


def test_dossier_rejects_invalid_counts_and_missing_rows():
    with pytest.raises(ValueError):
        generate_clinical_dossier((1, 1, 0), {})
    with pytest.raises(ValueError):
        generate_clinical_dossier((0, 0, 1, 1), {})


def test_dossier_localizes_narrative_and_embeds_all_available_figures():
    from ui.components import roc_plot_png_bytes
    counts = (25, 15, 7, 30)
    result = analyze_2x2(Table2x2(*counts))
    figure = forest_plot_png_bytes(result)
    roc = roc_plot_png_bytes(((0, 0, float("inf")), (0.2, 0.8, 0.5), (1, 1, float("-inf"))), 0.8)
    doc = Document(BytesIO(generate_clinical_dossier(
        counts, result, language="fr", forest_png=figure, roc_png=roc,
        fagan_png=figure, dca_png=figure, dual_roc_png=figure)))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Méthodes statistiques" in text
    assert "L’analyse comprenait" in text
    assert "Diagramme en forêt" in text
    assert len(doc.inline_shapes) == 5


def test_word_dossier_formats_small_p_values_and_embeds_association_forest_plot():
    from core.exporters import format_p_value
    from core.public_api import analyze_2x2

    assert format_p_value(None) == "—"
    assert format_p_value(0.00001) == "< 0.001"
    assert format_p_value(0.001) == "0.0010"
    assert format_p_value(0.05) == "0.0500"
    result = analyze_2x2((2, 100, 100, 2))
    payload = result.to_docx()
    document = Document(BytesIO(payload))
    table_text = " ".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
    assert "0.0000" not in table_text
    assert "< 0.001" in table_text
    assert len(document.inline_shapes) == 1
