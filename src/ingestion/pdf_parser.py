"""
Strukturierter, Section-Aware PDF Parser für wissenschaftliche Arbeiten.
Optimiert für mehrspaltige Layouts (PNAS, Nature, Science, IEEE, arXiv) mittels PyMuPDF.
Unterstützt intelligente Spaltensortierung, disziplinübergreifende Sektionserkennung
und OCR-Fallback für gescannte Dokumente via Gemini 3.6 Flash.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field
import pymupdf
import google.generativeai as genai

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

    # Disziplinübergreifende akademische Hauptabschnitte (Bio, Medizin, Physik, CS, ML)
    SECTION_PATTERNS: List[Tuple[str, str]] = [
        (r"(?i)\b(abstract|significance(?:\s+statement)?)\b", "Abstract & Significance"),
        (r"(?i)\b(\d+[\.\s]+)?(introduction|background)\b", "Introduction"),
        (r"(?i)\b(\d+[\.\s]+)?(related\s+work|literature\s+review)\b", "Related Work"),
        (r"(?i)\b(\d+[\.\s]+)?(materials?\s+and\s+methods|methods?|methodology|model\s+architecture|proposed\s+(?:method|approach|architecture))\b", "Methods & Architecture"),
        (r"(?i)\b(\d+[\.\s]+)?(experiments?|experimental\s+(?:setup|results)|benchmarks?|evaluation)\b", "Experiments & Benchmarks"),
        (r"(?i)\b(\d+[\.\s]+)?(results(?:\s+and\s+discussion)?)\b", "Results"),
        (r"(?i)\b(\d+[\.\s]+)?(discussion|analysis)\b", "Discussion"),
        (r"(?i)\b(\d+[\.\s]+)?(conclusions?|future\s+work|concluding\s+remarks)\b", "Conclusion"),
    ]

    # Abschnitte, die nicht indiziert werden sollen (Rauschunterdrückung)
    IGNORE_PATTERNS: List[str] = [
        r"(?i)\b(references|bibliography|works\s+cited)\b",
        r"(?i)\b(acknowledgments?|acknowledgements?)\b",
        r"(?i)\b(author\s+contributions?|competing\s+interests?|conflict\s+of\s+interest)\b",
    ]

    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150, api_key: Optional[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.api_key = api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def _detect_section(self, text: str, current_section: str) -> str:
        """Erkennt anhand von Überschriftenmustern, in welchem Abschnitt wir uns befinden."""
        lines = text.split("\n")
        for line in lines[:4]:
            clean_line = line.strip()
            if not clean_line:
                continue

            # Prüfen ob Stop-Abschnitt (References, Acknowledgments)
            for stop_pat in self.IGNORE_PATTERNS:
                if re.search(stop_pat, clean_line):
                    return "References"

            # Prüfen auf Fachabschnitte aller Disziplinen
            for pattern, canonical_name in self.SECTION_PATTERNS:
                if re.search(pattern, clean_line):
                    return canonical_name

        return current_section

    def _sort_blocks_by_reading_order(self, blocks: List[Any], page_width: float) -> List[str]:
        """
        Sortiert PyMuPDF Text-Blöcke intelligent nach Spalten.
        Verhindert das typische 2-Spalten-Vermischnungs-Problem von PDF-Readern.
        """
        text_blocks = [b for b in blocks if len(b) >= 5 and b[6] == 0 and b[4].strip()]
        if not text_blocks:
            return []

        # Ermitteln ob Seite ein 2-Spalten Layout hat
        mid_x = page_width / 2.0
        left_col = []
        right_col = []
        full_width = []

        for b in text_blocks:
            x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
            width = x1 - x0

            # Wenn Block breiter als 60% der Seite ist -> Titel, Abstract oder Footer
            if width > page_width * 0.60:
                full_width.append((y0, text))
            elif x1 <= mid_x + 20:
                left_col.append((y0, text))
            else:
                right_col.append((y0, text))

        # Sortierung:
        # 1. Volle Breite oben (Header / Titel / Abstract)
        # 2. Linke Spalte von oben nach unten
        # 3. Rechte Spalte von oben nach unten
        # 4. Volle Breite unten (Footer)
        top_full = [t for y, t in sorted(full_width, key=lambda x: x[0]) if y < 250]
        bottom_full = [t for y, t in sorted(full_width, key=lambda x: x[0]) if y >= 250]
        
        left_sorted = [t for y, t in sorted(left_col, key=lambda x: x[0])]
        right_sorted = [t for y, t in sorted(right_col, key=lambda x: x[0])]

        ordered_texts = top_full + left_sorted + right_sorted + bottom_full
        return ordered_texts

    def _ocr_page_with_gemini(self, page: Any) -> str:
        """Fallback für gescannte oder rein bildbasierte PDF-Seiten via Gemini Flash Vision."""
        if not self.api_key:
            return ""

        try:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-3.6-flash")
            response = model.generate_content([
                {"mime_type": "image/png", "data": img_bytes},
                "Extract all text from this scanned academic paper page faithfully. Keep numbers, table metrics and formulas intact."
            ])
            return response.text.strip()
        except Exception as e:
            print(f"[OCR Fallback Error] {e}")
            return ""

    def _split_into_chunks(self, text: str, page_num: int, paper_id: str, title: str, section: str) -> List[PaperChunk]:
        """Teilt Text in überlappende Chunks auf Satz- oder Absatzbasis."""
        chunks: List[PaperChunk] = []
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

                if len(para) > self.chunk_size:
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

    def extract_first_page_text(self, pdf_path: str) -> str:
        """Gibt den sauberen Text der ersten Seite für Metadaten-Extraktion zurück."""
        path = Path(pdf_path)
        if not path.exists():
            return ""

        doc = pymupdf.open(str(path))
        if len(doc) == 0:
            return ""

        first_page = doc[0]
        blocks = first_page.get_text("blocks")
        ordered = self._sort_blocks_by_reading_order(blocks, first_page.rect.width)
        raw_text = "\n\n".join(ordered)

        if len(raw_text.strip()) < 100 and self.api_key:
            raw_text = self._ocr_page_with_gemini(first_page)

        return raw_text

    def parse_pdf(self, pdf_path: str, paper_id: str, title: str) -> List[PaperChunk]:
        """
        Liest eine wissenschaftliche PDF mit PyMuPDF ein, sortiert Spalten sauber
        und erstellt semantische Chunks mit korrekten Sektions-Zuordnungen.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

        doc = pymupdf.open(str(path))
        all_chunks: List[PaperChunk] = []
        current_section = "Introduction"

        for page_idx, page in enumerate(doc):
            page_number = page_idx + 1
            blocks = page.get_text("blocks")
            ordered_texts = self._sort_blocks_by_reading_order(blocks, page.rect.width)
            page_text = "\n\n".join(ordered_texts).strip()

            # Erkennung von gescannten Seiten (< 80 Zeichen Text)
            if len(page_text) < 80 and len(page.get_images()) > 0:
                ocr_text = self._ocr_page_with_gemini(page)
                if ocr_text:
                    page_text = ocr_text

            if not page_text:
                continue

            # Sektionswechsel prüfen
            new_section = self._detect_section(page_text, current_section)
            
            # Literaturverzeichnis überspringen
            if new_section == "References":
                current_section = "References"
                continue

            current_section = new_section

            # Chunks generieren
            page_chunks = self._split_into_chunks(
                text=page_text,
                page_num=page_number,
                paper_id=paper_id,
                title=title,
                section=current_section
            )
            all_chunks.extend(page_chunks)

        return all_chunks
