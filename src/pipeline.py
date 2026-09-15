"""
ArXivLens Master RAG Pipeline.
Verbindet Ingestion, Vektorisierung, BM25, Hybrid RRF, FlashRank Re-Ranking und Google Gemini.
"""

from typing import List, Dict, Any, Optional, Generator, Tuple
from pathlib import Path

from .config import config
from .ingestion.arxiv_loader import ArxivPaperDownloader
from .ingestion.pdf_parser import SectionAwarePDFParser, PaperChunk
from .ingestion.metadata_extractor import MetadataExtractor
from .retrieval.embedding import GeminiEmbeddingClient
from .retrieval.vector_store import ChromaVectorStore
from .retrieval.bm25_index import BM25SearchIndex
from .retrieval.hybrid import HybridSearchEngine, SearchResult
from .retrieval.reranker import FlashRankReranker
from .generation.gemini_client import GeminiLLMClient
from .generation.prompts import PromptTemplates

class ArXivLensPipeline:
    """End-to-End RAG-Pipeline für wissenschaftliche Arbeiten."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key
        
        # Sub-Module initialisieren
        self.downloader = ArxivPaperDownloader()
        self.parser = SectionAwarePDFParser(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap, api_key=self.api_key)
        self.metadata_extractor = MetadataExtractor(api_key=self.api_key)
        self.embedding_client = GeminiEmbeddingClient(api_key=self.api_key)
        self.vector_store = ChromaVectorStore()
        self.bm25_index = BM25SearchIndex()
        self.hybrid_engine = HybridSearchEngine(rrf_k=config.rrf_k)
        self.reranker = FlashRankReranker(model_name=config.reranker_model_name)
        self.llm_client = GeminiLLMClient(api_key=self.api_key)

        # In-Memory Cache für geladene Papers
        self.indexed_papers: Dict[str, Dict[str, Any]] = {}

    def update_api_key(self, new_key: str):
        """Aktualisiert den Google API-Key über alle Module hinweg."""
        self.api_key = new_key
        self.parser.set_api_key(new_key)
        self.metadata_extractor.set_api_key(new_key)
        self.embedding_client.set_api_key(new_key)
        self.llm_client.set_api_key(new_key)

    def ingest_arxiv_paper(self, arxiv_query: str) -> Dict[str, Any]:
        """Lädt ein Paper via ArXiv ID herunter, parst es und indiziert Chunks."""
        metadata = self.downloader.fetch_paper(arxiv_query)
        paper_id = metadata["arxiv_id"]
        title = metadata["title"]
        pdf_path = metadata["local_pdf_path"]

        # PDF in strukturierte Chunks parsen
        chunks = self.parser.parse_pdf(pdf_path=pdf_path, paper_id=paper_id, title=title)
        if not chunks:
            raise ValueError(f"Aus der PDF von ArXiv '{paper_id}' konnten keine Chunks extrahiert werden.")

        # Embeddings via Google Gemini API berechnen
        chunk_texts = [c.text for c in chunks]
        embeddings = self.embedding_client.embed_documents(chunk_texts)

        # In ChromaDB und BM25 speichern
        self.vector_store.add_chunks(chunks, embeddings)
        self.bm25_index.add_chunks(chunks)

        self.indexed_papers[paper_id] = {
            **metadata,
            "journal": "arXiv",
            "chunk_count": len(chunks)
        }

        return {
            "paper_id": paper_id,
            "title": title,
            "chunk_count": len(chunks),
            "authors": metadata["authors"],
            "published": metadata["published"],
            "summary": metadata["summary"]
        }

    def ingest_uploaded_pdf(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """Parst eine vom Nutzer hochgeladene PDF-Datei, extrahiert Metadaten und indiziert sie."""
        paper_id = Path(filename).stem

        # 1. Erste Seite extrahieren & echte Metadaten (Titel, Autoren, Journal, DOI) gewinnen
        first_page_text = self.parser.extract_first_page_text(pdf_path)
        extracted = self.metadata_extractor.extract_with_llm(first_page_text, filename)

        title = extracted.title or paper_id.replace("_", " ").title()

        # 2. Strukturierte Chunks mit 2-Spalten-Sortierung extrahieren
        chunks = self.parser.parse_pdf(pdf_path=pdf_path, paper_id=paper_id, title=title)
        if not chunks:
            raise ValueError(f"Aus der PDF '{filename}' konnten keine Chunks extrahiert werden.")

        # 3. Embeddings berechnen & Indizieren
        chunk_texts = [c.text for c in chunks]
        embeddings = self.embedding_client.embed_documents(chunk_texts)

        self.vector_store.add_chunks(chunks, embeddings)
        self.bm25_index.add_chunks(chunks)

        metadata = {
            "arxiv_id": paper_id,
            "title": title,
            "authors": extracted.authors if extracted.authors else ["Wissenschaftliche Autoren"],
            "journal": extracted.journal,
            "published": extracted.published,
            "doi": extracted.doi,
            "summary": extracted.summary if extracted.summary else (chunks[0].text[:300] + "..."),
            "pdf_url": extracted.pdf_url or (f"https://doi.org/{extracted.doi}" if extracted.doi else None),
            "chunk_count": len(chunks),
            "local_pdf_path": pdf_path
        }
        self.indexed_papers[paper_id] = metadata

        return metadata

    def retrieve(
        self,
        query: str,
        paper_id: Optional[str] = None,
        use_reranker: bool = True
    ) -> List[SearchResult]:
        """
        Führt vollständiges Hybrid-Retrieval aus:
        1. Dense Vector Search (Google text-embedding-004)
        2. Sparse BM25 Keyword Search
        3. Reciprocal Rank Fusion (RRF)
        4. Optional: FlashRank Cross-Encoder Re-Ranking
        """
        # 1. Dense Search
        query_embedding = self.embedding_client.embed_query(query)
        dense_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=config.top_k_candidates,
            paper_id=paper_id
        )

        # 2. BM25 Search
        bm25_results = self.bm25_index.search(
            query=query,
            top_k=config.top_k_candidates,
            paper_id=paper_id
        )

        # 3. Hybrid Fusion via RRF
        fused_candidates = self.hybrid_engine.fuse(
            dense_results=dense_results,
            bm25_results=bm25_results,
            top_k=config.top_k_candidates
        )

        # 4. Re-Ranking (falls aktiviert)
        if use_reranker and fused_candidates:
            return self.reranker.rerank(
                query=query,
                results=fused_candidates,
                top_k=config.top_k_final
            )
        
        return fused_candidates[:config.top_k_final]

    def ask_stream(
        self,
        query: str,
        paper_id: Optional[str] = None,
        use_reranker: bool = True
    ) -> Tuple[Generator[str, None, None], List[SearchResult]]:
        """
        Führt Retrieval durch und liefert einen Streaming-Generator für die Antwort
        zusammen mit den abgerufenen Quellen-Chunks zurück.
        """
        chunks = self.retrieve(query=query, paper_id=paper_id, use_reranker=use_reranker)
        prompt = PromptTemplates.build_qa_prompt(query=query, context_chunks=chunks)
        stream_gen = self.llm_client.generate_stream(prompt=prompt)
        return stream_gen, chunks

    def generate_summary(self, paper_id: str) -> str:
        """Erstellt eine 1-Klick-Zusammenfassung für das angegebene Paper."""
        meta = self.indexed_papers.get(paper_id, {})
        title = meta.get("title", paper_id)
        abstract = meta.get("summary", "")

        # Die wichtigsten Chunks aus Methodik / Abstract abrufen
        key_chunks = self.retrieve(
            query="methodology architecture benchmark results innovation",
            paper_id=paper_id,
            use_reranker=True
        )

        prompt = PromptTemplates.build_summary_prompt(
            paper_title=title,
            abstract=abstract,
            key_chunks=key_chunks
        )
        return self.llm_client.generate(prompt=prompt)
