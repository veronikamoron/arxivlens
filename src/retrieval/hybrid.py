"""
Hybrid Search Engine mit Reciprocal Rank Fusion (RRF).
Kombiniert Dense Semantic Search und Sparse BM25 Keyword Search zu einer überlegenen Trefferliste.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..config import config

class SearchResult(BaseModel):
    """Einheitliches Ergebnis einer RAG-Suche."""
    chunk_id: str
    text: str
    paper_id: str
    title: str
    section: str
    page_number: int
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rrf_score: float = 0.0
    rerank_score: Optional[float] = None

class HybridSearchEngine:
    """Führt dichte und schlagwortbasierte Suche aus und fusioniert die Ränge via RRF."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k or config.rrf_k

    def fuse(
        self,
        dense_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Wendet Reciprocal Rank Fusion (RRF) auf die Ergebnisse beider Suchmethoden an.
        Formel: RRF_Score = 1 / (k + rank_dense) + 1 / (k + rank_bm25)
        """
        scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        # 1. Dense Ränge verarbeiten
        for rank, res in enumerate(dense_results, start=1):
            cid = res["chunk_id"]
            rrf_val = 1.0 / (self.rrf_k + rank)
            scores[cid] = scores.get(cid, 0.0) + rrf_val
            if cid not in chunks_map:
                chunks_map[cid] = res.copy()
            chunks_map[cid]["dense_score"] = res.get("dense_score")

        # 2. BM25 Ränge verarbeiten
        for rank, res in enumerate(bm25_results, start=1):
            cid = res["chunk_id"]
            rrf_val = 1.0 / (self.rrf_k + rank)
            scores[cid] = scores.get(cid, 0.0) + rrf_val
            if cid not in chunks_map:
                chunks_map[cid] = res.copy()
            chunks_map[cid]["bm25_score"] = res.get("bm25_score")

        # 3. Sortieren nach finalem RRF-Score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

        final_results: List[SearchResult] = []
        for cid in sorted_ids:
            data = chunks_map[cid]
            final_results.append(SearchResult(
                chunk_id=cid,
                text=data["text"],
                paper_id=data.get("paper_id", ""),
                title=data.get("title", ""),
                section=data.get("section", ""),
                page_number=data.get("page_number", 1),
                dense_score=data.get("dense_score"),
                bm25_score=data.get("bm25_score"),
                rrf_score=round(scores[cid], 5)
            ))

        return final_results
