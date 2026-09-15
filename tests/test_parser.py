"""
Tests für Section-Aware PDF Parsing und Chunking.
"""

import pytest
from src.ingestion.pdf_parser import SectionAwarePDFParser, PaperChunk

def test_section_detection():
    """Testet die Erkennung typischer akademischer Überschriften."""
    parser = SectionAwarePDFParser()
    
    assert parser._detect_section("1. Introduction to Attention Mechanisms", "Unknown") == "Introduction"
    assert parser._detect_section("3. Model Architecture and Multi-Head Attention", "Unknown") == "Methods & Architecture"
    assert parser._detect_section("4. Experimental Results on WMT 2014", "Unknown") == "Experiments & Benchmarks"
    assert parser._detect_section("Significance Statement\nKey discovery in neuroscience", "Unknown") == "Abstract & Significance"
    assert parser._detect_section("Materials and Methods\nCell cultures were prepared", "Unknown") == "Methods & Architecture"
    assert parser._detect_section("Results\nOur analysis revealed significant activation", "Unknown") == "Results"
    assert parser._detect_section("References\n[1] Vaswani et al.", "Introduction") == "References"

def test_chunking_preserves_metadata():
    """Prüft, ob Chunks alle relevanten Metadaten für das Retrieval behalten."""
    parser = SectionAwarePDFParser(chunk_size=200, chunk_overlap=20)
    sample_text = (
        "The Transformer is the first transduction model relying entirely on self-attention "
        "to compute representations of its input and output without using sequence-aligned RNNs or convolution. "
        "In the following sections, we will describe the Transformer architecture and experimental results."
    )
    
    chunks = parser._split_into_chunks(
        text=sample_text,
        page_num=1,
        paper_id="1706.03762",
        title="Attention Is All You Need",
        section="Introduction"
    )
    
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.paper_id == "1706.03762"
    assert chunk.title == "Attention Is All You Need"
    assert chunk.section == "Introduction"
    assert chunk.page_number == 1
    assert "Transformer" in chunk.text

def test_stop_at_references():
    """Stellt sicher, dass Literaturverzeichnisse nicht mitindiziert werden."""
    parser = SectionAwarePDFParser()
    assert parser._detect_section("References", "Conclusion") == "References"
    assert parser._detect_section("Bibliography", "Conclusion") == "References"
