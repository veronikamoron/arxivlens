"""
ArXiv Paper Downloader & Metadata Fetcher.
Ermöglicht das automatische Herunterladen von Papers via ArXiv ID oder URL.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
import arxiv

class ArxivPaperDownloader:
    """Lädt wissenschaftliche Arbeiten von ArXiv herunter und extrahiert Metadaten."""

    # Populäre Meilenstein-Papers für den 1-Klick Quickstart
    PRESET_PAPERS = {
        "1706.03762": {
            "id": "1706.03762",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"],
            "summary": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks... We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism.",
            "year": 2017
        },
        "2005.11401": {
            "id": "2005.11401",
            "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
            "authors": ["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus", "Fabio Petroni", "Vladimir Karpukhin", "Naman Goyal", "Heinrich Küttler", "Mike Lewis", "Wen-tau Yih", "Tim Rocktäschel", "Sebastian Riedel", "Douwe Kiela"],
            "summary": "Large pre-trained language models have been shown to store factual knowledge in their parameters... We explore retrieval-augmented generation (RAG) models which combine pre-trained parametric and non-parametric memory.",
            "year": 2020
        }
    }

    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_arxiv_id(query: str) -> Optional[str]:
        """Extrahiert eine ArXiv-ID aus verschiedenen Formaten (z.B. '1706.03762', 'arxiv:1706.03762', 'https://arxiv.org/abs/1706.03762')."""
        clean = query.strip()
        # Regex für moderne ArXiv IDs (z.B. 1706.03762 oder mit Versionsnummer 1706.03762v2)
        match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", clean)
        if match:
            return match.group(1)
        # Ältere ArXiv IDs (z.B. hep-th/9912012)
        match_old = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})", clean)
        if match_old:
            return match_old.group(1)
        return None

    def fetch_paper(self, query: str) -> Dict[str, Any]:
        """
        Sucht ein Paper via ArXiv ID und lädt die PDF herunter.
        Gibt ein Dictionary mit Metadaten und dem lokalen Dateipfad zurück.
        """
        arxiv_id = self.extract_arxiv_id(query)
        if not arxiv_id:
            raise ValueError(f"Ungültige ArXiv ID oder URL: '{query}'. Beispiel: '1706.03762' oder 'https://arxiv.org/abs/1706.03762'")

        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(client.results(search))

        if not results:
            raise ValueError(f"Kein ArXiv-Paper mit der ID '{arxiv_id}' gefunden.")

        paper = results[0]
        safe_filename = f"{arxiv_id.replace('/', '_')}.pdf"
        pdf_path = self.download_dir / safe_filename

        # Direkter, nativer Download der PDF via urllib (unabhängig von arxiv-Bibliotheksversionen)
        if not pdf_path.exists():
            import urllib.request
            pdf_url = getattr(paper, "pdf_url", f"https://arxiv.org/pdf/{arxiv_id}.pdf")
            req = urllib.request.Request(
                pdf_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ArXivLens/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(pdf_path, "wb") as f:
                f.write(resp.read())


        return {
            "arxiv_id": arxiv_id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d") if paper.published else "Unknown",
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "local_pdf_path": str(pdf_path)
        }
