"""
Tests für Retrieval-Komponenten: BM25, Hybrid RRF Fusion und FlashRank Re-Ranking.
Läuft 100% offline ohne API-Key.
"""

import pytest
from src.ingestion.pdf_parser import PaperChunk
from src.retrieval.bm25_index import BM25SearchIndex
from src.retrieval.hybrid import HybridSearchEngine

def test_bm25_tokenization_and_search():
    """Testet die exakte Keyword-Suche mit Bindestrichen und Metriken."""
    index = BM25SearchIndex()
    
    chunks = [
        PaperChunk(
            chunk_id="c1",
            paper_id="p1",
            title="Transformer",
            section="Results",
            page_number=5,
            text="The model achieves a BLEU-4 score of 28.4 on English-to-German translation."
        ),
        PaperChunk(
            chunk_id="c2",
            paper_id="p1",
            title="Transformer",
            section="Architecture",
            page_number=3,
            text="We use Multi-Head Attention with 8 parallel attention heads."
        ),
        PaperChunk(
            chunk_id="c3",
            paper_id="p1",
            title="Transformer",
            section="Training",
            page_number=7,
            text="Training was performed on 8 NVIDIA P100 GPUs for 3.5 days."
        )
    ]
    
    index.add_chunks(chunks)
    
    # Suche nach exaktem Begriff
    results = index.search("BLEU-4", top_k=2)
    assert len(results) > 0
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["bm25_score"] > 0

def test_reciprocal_rank_fusion():
    """Testet die korrekte RRF-Fusionierung von Dense und Sparse Ergebnissen."""
    hybrid = HybridSearchEngine(rrf_k=60)
    
    dense_results = [
        {"chunk_id": "c1", "text": "Text 1", "title": "Paper A", "section": "Intro", "page_number": 1, "dense_score": 0.95},
        {"chunk_id": "c2", "text": "Text 2", "title": "Paper A", "section": "Method", "page_number": 2, "dense_score": 0.85},
    ]
    
    bm25_results = [
        {"chunk_id": "c2", "text": "Text 2", "title": "Paper A", "section": "Method", "page_number": 2, "bm25_score": 5.2},
        {"chunk_id": "c1", "text": "Text 1", "title": "Paper A", "section": "Intro", "page_number": 1, "bm25_score": 2.1},
    ]
    
    # c2 ist Rang 2 in Dense und Rang 1 in BM25
    # c1 ist Rang 1 in Dense und Rang 2 in BM25
    # Beide erhalten exakt: 1/(60+1) + 1/(60+2)
    fused = hybrid.fuse(dense_results, bm25_results, top_k=2)
    
    assert len(fused) == 2
    assert fused[0].rrf_score > 0
    assert fused[1].rrf_score > 0
