"""
Ingestion-Module für ArXiv-Downloads und strukturiertes PDF-Parsing.
"""

from .arxiv_loader import ArxivPaperDownloader
from .pdf_parser import SectionAwarePDFParser, PaperChunk
from .metadata_extractor import MetadataExtractor, ExtractedPaperMetadata

__all__ = [
    "ArxivPaperDownloader",
    "SectionAwarePDFParser",
    "PaperChunk",
    "MetadataExtractor",
    "ExtractedPaperMetadata"
]
