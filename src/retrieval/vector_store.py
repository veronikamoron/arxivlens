"""
ChromaDB Vektordatenbank Wrapper (Lokaler Persistenz-Modus).
Speichert Chunks, Metadaten und Dense Embeddings sicher auf der lokalen Festplatte.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from ..ingestion.pdf_parser import PaperChunk
from ..config import config

class ChromaVectorStore:
    """Verwaltet Vektor-Speicher und semantische Similarity-Suchen via ChromaDB."""

    COLLECTION_NAME = "arxiv_papers"

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or config.chroma_dir
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Lokaler Chroma-Client ohne Telemetrie für maximale Privatsphäre
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[PaperChunk], embeddings: List[List[float]]):
        """Fügt Chunks und die zugehörigen Embeddings zur Collection hinzu."""
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "paper_id": c.paper_id,
                "title": c.title,
                "section": c.section,
                "page_number": c.page_number
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(self, query_embedding: List[float], top_k: int = 10, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Führt eine Cosine-Similarity-Vektorsuche durch.
        Kann optional nach einem spezifischen Paper gefiltert werden.
        """
        where_filter = {"paper_id": paper_id} if paper_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        formatted: List[Dict[str, Any]] = []
        if not results["ids"] or not results["ids"][0]:
            return formatted

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(ids)):
            # Cosine Distance in Similarity Score umwandeln (1.0 - distance)
            score = 1.0 - distances[i] if distances else 0.0
            formatted.append({
                "chunk_id": ids[i],
                "text": docs[i],
                "paper_id": metas[i].get("paper_id", ""),
                "title": metas[i].get("title", ""),
                "section": metas[i].get("section", ""),
                "page_number": metas[i].get("page_number", 1),
                "dense_score": float(score)
            })

        return formatted

    def count(self) -> int:
        """Gibt die Gesamtanzahl der indizierten Chunks zurück."""
        return self.collection.count()

    def clear(self):
        """Löscht alle Chunks aus der Collection."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
