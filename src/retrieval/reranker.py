"""
FlashRank Cross-Encoder Re-Ranker.
Extrem schneller, lokaler CPU-basierter Re-Ranker für die präziseste Chunk-Auswahl.
"""

from typing import List, Optional
from flashrank import Ranker, RerankRequest
from .hybrid import SearchResult
from ..config import config

class FlashRankReranker:
    """Führt Cross-Encoder Re-Ranking auf CPU ohne PyTorch/GPU-Overhead durch."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.reranker_model_name
        self._ranker: Optional[Ranker] = None

    @property
    def ranker(self) -> Ranker:
        """Lazy-Loading des Rankers beim ersten Aufruf."""
        if self._ranker is None:
            self._ranker = Ranker(model_name=self.model_name, cache_dir="./.cache/flashrank")
        return self._ranker

    def rerank(self, query: str, results: List[SearchResult], top_k: int = 4) -> List[SearchResult]:
        """
        Bewertet die übergebenen Chunks mit einem Cross-Encoder neu.
        Gibt die Top-K präzisesten Chunks zurück.
        """
        if not results:
            return []

        # Passages für FlashRank vorbereiten
        passages = [
            {"id": res.chunk_id, "text": res.text, "meta": res.model_dump()}
            for res in results
        ]

        try:
            rerank_request = RerankRequest(query=query, passages=passages)
            reranked_output = self.ranker.rerank(rerank_request)

            final_results: List[SearchResult] = []
            for item in reranked_output[:top_k]:
                orig_meta = item["meta"]
                score = float(item["score"])
                final_results.append(SearchResult(
                    chunk_id=orig_meta["chunk_id"],
                    text=orig_meta["text"],
                    paper_id=orig_meta["paper_id"],
                    title=orig_meta["title"],
                    section=orig_meta["section"],
                    page_number=orig_meta["page_number"],
                    dense_score=orig_meta.get("dense_score"),
                    bm25_score=orig_meta.get("bm25_score"),
                    rrf_score=orig_meta.get("rrf_score", 0.0),
                    rerank_score=round(score, 4)
                ))

            return final_results
        except Exception as e:
            # Fallback bei unerwartetem Fehler: Original-Ergebnisse zurückgeben
            print(f"[FlashRank Warning] Re-Ranking fehlgeschlagen ({e}), verwende RRF-Sortierung.")
            return results[:top_k]
