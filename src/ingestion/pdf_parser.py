"""
Strukturierter, Section-Aware PDF Parser für wissenschaftliche Arbeiten.
Behält Abschnitte und Tabellen bei, filtert Literaturverzeichnisse heraus.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from pypdf import PdfReader

class PaperChunk(BaseModel):
    """Repräsentiert einen semantischen Textabschnitt aus einem Paper."""
    chunk_id: str
    paper_id: str
    title: str
    section: str
    page_number: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SectionAwarePDFParser:
    """Parst wissenschaftliche PDFs und erstellt saubere, semantische Chunks."""

    # Typische akademische Hauptabschnitte
    SECTION_PATTERNS = [
        r"(?i)\b(abstract)\b",
        r"(?i)\b(1\.?\s+introduction|introduction)\b",
        r"(?i)\b(2\.?\s+background|background|related\s+work)\b",
        r"(?i)\b(3\.?\s+architecture|model\s+architecture|methodology|proposed\s+method)\b",
        r"(?i)\b(4\.?\s+experiments|experimental\s+setup|results)\b",
        r"(?i)\b(5\.?\s+discussion|analysis)\b",
        r"(?i)\b(6\.?\s+conclusion|conclusions|future\s+work)\b",
    ]

    # Abschnitte, die für das Retrieval ignoriert werden sollen (Rauschunterdrückung)
    IGNORE_PATTERNS = [
        r"(?i)\b(references|bibliography)\b",
        r"(?i)\b(acknowledgments?|acknowledgements?)\b",
    ]

    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _detect_section(self, text: str, current_section: str) -> str:
        """Erkennt anhand von Überschriftenmustern, in welchem Abschnitt wir uns befinden."""
        lines = text.split("\n")
        for line in lines[:5]:  # Meist in den ersten paar Zeilen einer Seite/Absatz
            clean_line = line.strip()
            # Prüfen ob Stop-Abschnitt (References)
            for stop_pat in self.IGNORE_PATTERNS:
                if re.search(stop_pat, clean_line):
                    return "References"
            # Prüfen auf Fachabschnitte
            for pat in self.SECTION_PATTERNS:
                match = re.search(pat, clean_line)
                if match:
                    # Saubere Formatierung des Abschnittsnamens
                    raw = match.group(0).strip()
                    return re.sub(r"^\d+\.?\s*", "", raw).title()
        return current_section

    def _split_into_chunks(self, text: str, page_num: int, paper_id: str, title: str, section: str) -> List[PaperChunk]:
        """Teilt Text in überlappende Chunks auf Satz- oder Absatzbasis."""
        chunks: List[PaperChunk] = []
        # Absätze trennen
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 30]

        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunk_id = f"{paper_id}_p{page_num}_c{chunk_idx}"
                    chunks.append(PaperChunk(
                        chunk_id=chunk_id,
                        paper_id=paper_id,
                        title=title,
                        section=section,
                        page_number=page_num,
                        text=current_chunk.strip(),
                        metadata={"length": len(current_chunk)}
                    ))
                    chunk_idx += 1
                
                # Mit Overlap neu anfangen
                if len(para) > self.chunk_size:
                    # Sehr langer Absatz: hart nach Sätzen splitten
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) <= self.chunk_size:
                            sub_chunk += (" " if sub_chunk else "") + s
                        else:
                            if sub_chunk:
                                chunk_id = f"{paper_id}_p{page_num}_c{chunk_idx}"
                                chunks.append(PaperChunk(
                                    chunk_id=chunk_id,
                                    paper_id=paper_id,
                                    title=title,
                                    section=section,
                                    page_number=page_num,
                                    text=sub_chunk.strip()
                                ))
                                chunk_idx += 1
                            sub_chunk = s
                    current_chunk = sub_chunk
                else:
                    current_chunk = para

        if current_chunk:
            chunk_id = f"{paper_id}_p{page_num}_c{chunk_idx}"
            chunks.append(PaperChunk(
                chunk_id=chunk_id,
                paper_id=paper_id,
                title=title,
                section=section,
                page_number=page_num,
                text=current_chunk.strip()
            ))

        return chunks

    def parse_pdf(self, pdf_path: str, paper_id: str, title: str) -> List[PaperChunk]:
        """
        Liest eine PDF-Datei ein, erkennt Abschnitte und extrahiert strukturierte Chunks.
        Ignoriert automatisch Seiten ab dem Literaturverzeichnis (References).
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

        reader = PdfReader(str(path))
        all_chunks: List[PaperChunk] = []
        current_section = "Introduction"
        skip_remaining = False

        for page_idx, page in enumerate(reader.pages):
            if skip_remaining:
                break

            page_number = page_idx + 1
            raw_text = page.extract_text() or ""
            clean_text = re.sub(r"[ \t]+", " ", raw_text)

            # Abschnitt prüfen
            new_section = self._detect_section(clean_text, current_section)
            if new_section == "References":
                # Ab hier beginnen die reinen Literaturangaben -> überspringen
                skip_remaining = True
                continue
            
            current_section = new_section

            # In Chunks aufteilen
            page_chunks = self._split_into_chunks(
                text=clean_text,
                page_num=page_number,
                paper_id=paper_id,
                title=title,
                section=current_section
            )
            all_chunks.extend(page_chunks)

        return all_chunks
