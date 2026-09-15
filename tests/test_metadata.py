"""
Unit-Tests für den MetadataExtractor (DOI, Journal-Erkennung, Jahreszahlen, Fallback).
Läuft 100% offline ohne API-Key.
"""

import pytest
from src.ingestion.metadata_extractor import MetadataExtractor

def test_doi_extraction():
    """Testet das Auffinden wissenschaftlicher Digital Object Identifiers."""
    extractor = MetadataExtractor()
    sample_pnas = (
        "PNAS 2025 Vol. 122 No. 12 e202524065\n"
        "https://doi.org/10.1073/pnas.202524065\n"
        "Neural representations of subjective value in the human cortex"
    )
    data = extractor.extract_heuristics(sample_pnas, "pnas.202524065.pdf")
    assert data["doi"] == "10.1073/pnas.202524065"
    assert data["journal"] == "PNAS"
    assert data["year"] == "2025"

def test_journal_detection_variants():
    """Testet die Klassifizierung verschiedener Verlage und Preprint-Server."""
    extractor = MetadataExtractor()
    
    nature_sample = "Nature Communications | (2024) 15:1234 | https://doi.org/10.1038/s41467-024-00123-x"
    data_nature = extractor.extract_heuristics(nature_sample, "nature_paper.pdf")
    assert data_nature["journal"] == "Nature Communications"
    assert data_nature["doi"] == "10.1038/s41467-024-00123-x"
    assert data_nature["year"] == "2024"

    ieee_sample = "IEEE Transactions on Neural Networks and Learning Systems, 2023. DOI: 10.1109/TNNLS.2023.12345"
    data_ieee = extractor.extract_heuristics(ieee_sample, "ieee_paper.pdf")
    assert data_ieee["journal"] == "IEEE"
    assert data_ieee["year"] == "2023"

def test_heuristics_fallback_without_api_key():
    """Stellt sicher, dass bei fehlendem API-Key immer gültige Metadaten zurückgegeben werden."""
    extractor = MetadataExtractor(api_key=None)
    result = extractor.extract_with_llm("Random paper text without header", "my_research_notes.pdf")
    
    assert result.paper_id == "my_research_notes"
    assert result.title != ""
    assert result.published == "2024"
    assert len(result.authors) >= 1
