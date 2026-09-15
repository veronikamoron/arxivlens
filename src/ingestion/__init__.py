"""
Ingestion-Module für ArXiv-Downloads und strukturiertes PDF-Parsing.
"""

from .arxiv_loader import ArxivPaperDownloader
from .pdf_parser import SectionAwarePDFParser, PaperChunk

__all__ = ["ArxivPaperDownloader", "SectionAwarePDFParser", "PaperChunk"]
