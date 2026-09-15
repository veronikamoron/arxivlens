"""
Intelligenter Metadaten-Extraktor für wissenschaftliche PDFs.
Erkennt echten Titel, Autoren, Journal (z.B. PNAS, Nature, IEEE), DOI und Erscheinungsjahr
über einen hybriden Ansatz aus visuellem PyMuPDF-Layout-Parsing (Font-Größen & Koordinaten)
und strukturiertem Gemini Flash Parsing.
"""

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import pymupdf
import google.generativeai as genai

class ExtractedPaperMetadata(BaseModel):
    """Strukturierte Metadaten einer wissenschaftlichen Arbeit."""
    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    journal: str = "Peer-Reviewed Paper"
    published: str = "2024"
    doi: Optional[str] = None
    summary: str = ""
    pdf_url: Optional[str] = None

class MetadataExtractor:
    """Extrahiert akkurate Metadaten aus wissenschaftlichen Arbeiten."""

    DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
    YEAR_PATTERN = re.compile(r"\b(20[0-2]\d|19\d\d)\b")
    
    # Bekannte Zeitschriften & Verlage
    JOURNAL_PATTERNS = [
        (re.compile(r"(?i)\b(proceedings of the national academy of sciences|pnas)\b"), "PNAS"),
        (re.compile(r"(?i)\b(nature communications)\b"), "Nature Communications"),
        (re.compile(r"(?i)\b(nature medicine|nature biotechnology|nature genetics|nature neuroscience|nature methods)\b"), "Nature"),
        (re.compile(r"(?i)\b(nature)\b"), "Nature"),
        (re.compile(r"(?i)\b(science advances)\b"), "Science Advances"),
        (re.compile(r"(?i)\b(science)\b"), "Science"),
        (re.compile(r"(?i)\b(cell|cell reports)\b"), "Cell"),
        (re.compile(r"(?i)\b(ieee transactions[a-z\s]*|ieee)\b"), "IEEE"),
        (re.compile(r"(?i)\b(acm transactions[a-z\s]*|acm)\b"), "ACM"),
        (re.compile(r"(?i)\b(plos one|plos computational biology)\b"), "PLOS"),
        (re.compile(r"(?i)\barxiv:\s*(\d{4}\.\d{4,5})\b"), "arXiv"),
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def extract_from_layout(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Extrahiert Metadaten rein deterministisch und offline anhand der visuellen
        Schriftgrößen-Hierarchie von PyMuPDF (der Titel hat immer die größte Schriftgröße).
        """
        paper_id = Path(filename).stem
        path = Path(pdf_path)
        if not path.is_file():
            return {
                "title": paper_id.replace("_", " ").title(),
                "authors": ["Wissenschaftliche Autoren"],
                "journal": "Academic Paper",
                "doi": None,
                "year": "2024",
                "summary": ""
            }

        doc = pymupdf.open(str(path))
        if len(doc) == 0:
            return {
                "title": paper_id.replace("_", " ").title(),
                "authors": ["Wissenschaftliche Autoren"],
                "journal": "Academic Paper",
                "doi": None,
                "year": "2024",
                "summary": ""
            }

        page = doc[0]
        data = page.get_text("dict")
        page_text = page.get_text("text")

        # 1. Alle Text-Spans mit Größen und Koordinaten sammeln
        spans = []
        for b in data.get("blocks", []):
            if "lines" in b:
                for line in b["lines"]:
                    for span in line["spans"]:
                        t = span["text"].replace("\xa0", " ").strip()
                        if t:
                            spans.append({
                                "text": t,
                                "size": span["size"],
                                "flags": span["flags"],
                                "bbox": span["bbox"]
                            })

        # 2. Titel anhand der maximalen Schriftgröße auf Seite 1 ermitteln
        title = paper_id.replace("_", " ").title()
        title_y1 = 150.0

        if spans:
            max_size = max(s["size"] for s in spans)
            title_spans = [s for s in spans if abs(s["size"] - max_size) < 1.0]
            raw_title = " ".join(s["text"] for s in title_spans).strip()
            # Unerwünschte Banner entfernen
            cleaned_title = re.sub(r"(?i)^(research article|review article|open access|article|report)\s*[|•\-–—]\s*", "", raw_title).strip()
            cleaned_title = re.sub(r"(?i)\s*[|•\-–—]\s*(open access|research article|neuroscience)", "", cleaned_title).strip()
            if len(cleaned_title) > 5:
                title = cleaned_title
                title_y1 = max(s["bbox"][3] for s in title_spans)

        # 3. Autoren suchen: Spans direkt unter dem Titel
        authors: List[str] = []
        author_spans = []
        for s in spans:
            if title_y1 < s["bbox"][1] < title_y1 + 110:
                txt = s["text"]
                if any(stop in txt.lower() for stop in ["affiliation", "abstract", "significance", "edited by", "received", "published", "copyright"]):
                    break
                author_spans.append(txt)

        if author_spans:
            raw_author_str = " ".join(author_spans)
            # Bereinigung von hochgestellten Ziffern und Affiliation-Buchstaben (z.B. 'a,b', '1')
            clean_author_str = re.sub(r"\b[a-z0-9,]+\b(?=\s*[,]|and|\s*$)", "", raw_author_str)
            raw_splits = re.split(r"[,;]|\band\b", clean_author_str)
            for a in raw_splits:
                a_clean = re.sub(r"[^a-zA-Z\s\.\-]", "", a).strip()
                if len(a_clean) > 2 and not any(kw in a_clean.lower() for kw in ["open access", "research", "neuroscience", "affiliations"]):
                    authors.append(a_clean)

        if not authors:
            authors = ["Wissenschaftliche Autoren"]

        # 4. DOI suchen (vollständigste/längste DOI auf Seite 1)
        doi_matches = self.DOI_PATTERN.findall(page_text)
        valid_dois = [d.rstrip(".") for d in doi_matches if not d.endswith("pnas.") and len(d) > 12]
        doi = valid_dois[0] if valid_dois else (doi_matches[0].rstrip(".") if doi_matches else None)

        # 5. Journal bestimmen
        journal = "Peer-Reviewed Paper"
        for pattern, j_name in self.JOURNAL_PATTERNS:
            if pattern.search(page_text):
                journal = j_name
                break

        # 6. Jahr ermitteln (aus DOI oder Text)
        year_matches = self.YEAR_PATTERN.findall(page_text)
        year = year_matches[0] if year_matches else "2024"

        return {
            "title": title[:160],
            "authors": authors[:8],
            "journal": journal,
            "doi": doi,
            "year": year,
            "summary": page_text[:400].strip() + "..."
        }

    def extract_heuristics(self, first_page_text: str, filename: str) -> Dict[str, Any]:
        """Kompatibilitäts-Fallback wenn nur der Rohtext vorliegt."""
        paper_id = Path(filename).stem
        doi_matches = self.DOI_PATTERN.findall(first_page_text)
        valid_dois = [d.rstrip(".") for d in doi_matches if not d.endswith("pnas.") and len(d) > 12]
        doi = valid_dois[0] if valid_dois else (doi_matches[0].rstrip(".") if doi_matches else None)

        journal = "Academic Paper"
        for pattern, j_name in self.JOURNAL_PATTERNS:
            if pattern.search(first_page_text):
                journal = j_name
                break

        year_matches = self.YEAR_PATTERN.findall(first_page_text[:1500])
        year = year_matches[0] if year_matches else "2024"

        lines = [line.strip() for line in first_page_text.split("\n") if len(line.strip()) > 5]
        cleaned_lines = []
        for line in lines[:12]:
            l_lower = line.lower()
            if not any(stop in l_lower for stop in ["http", "doi.org", "vol.", "issue", "pnas", "www.", "copyright", "downloaded from"]):
                clean = re.sub(r"(?i)^(research article|review article|open access|article|report)\s*[|•\-–—]\s*", "", line).strip()
                clean = re.sub(r"(?i)\s*[|•\-–—]\s*(open access|research article|neuroscience)", "", clean).strip()
                if len(clean) > 8:
                    cleaned_lines.append(clean)

        fallback_title = cleaned_lines[0] if cleaned_lines else paper_id.replace("_", " ").title()

        return {
            "title": fallback_title[:150],
            "authors": ["Wissenschaftliche Autoren"],
            "journal": journal,
            "doi": doi,
            "year": year,
            "summary": first_page_text[:400].strip() + "..."
        }

    def extract_metadata(self, pdf_path: str, filename: str, first_page_text: Optional[str] = None) -> ExtractedPaperMetadata:
        """
        Hauptmethode: Kombiniert visuelles PyMuPDF Layout-Parsing mit optionalem
        Gemini 3.6 Flash Structured Output.
        """
        paper_id = Path(filename).stem
        path = Path(pdf_path)
        if path.is_file():
            layout_data = self.extract_from_layout(pdf_path, filename)
        elif first_page_text:
            layout_data = self.extract_heuristics(first_page_text, filename)
        else:
            layout_data = self.extract_from_layout(pdf_path, filename)

        title = layout_data["title"]
        authors = layout_data["authors"]
        journal = layout_data["journal"]
        doi = layout_data["doi"]
        year = layout_data["year"]
        summary = layout_data["summary"]

        # Falls ein API-Key vorhanden ist, lassen wir Gemini Flash die Details verfeinern
        if self.api_key and first_page_text and len(first_page_text.strip()) > 100:
            prompt = f"""Du bist ein akademischer Metadaten-Parser.
Analysiere die erste Seite dieser wissenschaftlichen Arbeit und extrahiere die exakten bibliographischen Daten.

TEXT DER ERSTEN SEITE:
\"\"\"
{first_page_text[:3500]}
\"\"\"

ANTWORTE AUSSCHLIESSLICH IM FOLGENDEN JSON-FORMAT (kein Markdown, keine Erklärung):
{{
  "title": "Der vollständige, exakte wissenschaftliche Titel des Papers",
  "authors": ["Vorname Nachname", "Vorname Nachname"],
  "journal": "Name der Zeitschrift (z.B. PNAS, Nature, Science, IEEE, arXiv oder Peer-Reviewed Journal)",
  "doi": "DOI falls vorhanden (z.B. 10.1073/pnas.2524065123), sonst null",
  "year": "YYYY (z.B. 2026)",
  "abstract": "Kurze Zusammenfassung oder Abstract / Significance Statement (2-3 Sätze)"
}}
"""
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-3.6-flash",
                    generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
                )
                response = model.generate_content(prompt)
                data = json.loads(response.text.strip())

                title = data.get("title") or title
                if data.get("authors") and isinstance(data["authors"], list):
                    authors = data["authors"]
                journal = data.get("journal") or journal
                doi = data.get("doi") or doi
                year = str(data.get("year") or year)
                summary = data.get("abstract") or summary
            except Exception as e:
                print(f"[MetadataExtractor Info] LLM-Verfeinerung übersprungen ({e}). Verwende Layout-Metadaten.")

        pdf_url = f"https://doi.org/{doi}" if doi else (f"https://arxiv.org/abs/{paper_id}" if journal == "arXiv" else None)

        return ExtractedPaperMetadata(
            paper_id=paper_id,
            title=title,
            authors=authors,
            journal=journal,
            published=year,
            doi=doi,
            summary=summary,
            pdf_url=pdf_url
        )

    def extract_with_llm(self, first_page_text: str, filename: str) -> ExtractedPaperMetadata:
        """Alias für Kompatibilität mit Text-Aufrufen."""
        return self.extract_metadata("", filename, first_page_text)
