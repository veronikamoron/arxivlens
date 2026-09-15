"""
BM25 Keyword Search Index (Sparse Retrieval).
Ergänzt die Vektorsuche ideal bei exakten Begriffen, Modellkürzeln, Tabellen und Metriken.
"""

import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from ..ingestion.pdf_parser import PaperChunk

class BM25SearchIndex:
    """In-Memory BM25 Index für exakte Keyword-Suche."""

    def __init__(self):
        self.chunks: List[PaperChunk] = []
        self.corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenisiert Text für wissenschaftliche Abfragen.
        Erhält Modellnamen und Metriken mit Bindestrichen (z.B. 'llama-3', 'bleu-4', 'mmlu').
        """
        text_clean = text.lower()
        # Findet Wörter inklusive Bindestriche und Zahlen
        tokens = re.findall(r"\b[a-z0-9]+(?:[-_][a-z0-9]+)*\b", text_clean)
        return tokens

    def add_chunks(self, chunks: List[PaperChunk]):
        """Fügt neue Chunks zum Index hinzu und baut den BM25-Index auf."""
        self.chunks.extend(chunks)
        tokenized_corpus = [self.tokenize(c.text) for c in self.chunks]
        self.corpus = tokenized_corpus
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 10, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Führt eine BM25 Keyword-Suche durch.
        Gibt die Top-K passenden Chunks mit BM25-Score zurück.
        """
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Chunks mit Scores verknüpfen
        scored_chunks = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            if paper_id and chunk.paper_id != paper_id:
                continue
            if score > 0:  # Nur Treffer mit Relevanz
                scored_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "paper_id": chunk.paper_id,
                    "title": chunk.title,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "bm25_score": float(score)
                })

        # Nach Score absteigend sortieren
        scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:top_k]

    def clear(self):
        """Setzt den Index zurück."""
        self.chunks = []
        self.corpus = []
        self.bm25 = None
