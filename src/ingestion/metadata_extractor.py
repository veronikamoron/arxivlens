"""
Intelligenter Metadaten-Extraktor für wissenschaftliche PDFs.
Erkennt echten Titel, Autoren, Journal (z.B. PNAS, Nature, IEEE), DOI und Erscheinungsjahr
über einen hybriden Ansatz aus Regex-Heuristiken und strukturiertem Gemini Flash Parsing.
"""

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
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

    def extract_heuristics(self, first_page_text: str, filename: str) -> Dict[str, Any]:
        """Offline-Extraktion über reguläre Ausdrücke und Textstruktur."""
        paper_id = Path(filename).stem

        # 1. DOI suchen
        doi_match = self.DOI_PATTERN.search(first_page_text)
        doi = doi_match.group(1).rstrip(".") if doi_match else None

        # 2. Journal ermitteln
        journal = "Academic Paper"
        for pattern, j_name in self.JOURNAL_PATTERNS:
            if pattern.search(first_page_text):
                journal = j_name
                break

        # 3. Jahr ermitteln
        year_matches = self.YEAR_PATTERN.findall(first_page_text[:1500])
        year = year_matches[0] if year_matches else "2024"

        # 4. Titel & Autoren heuristisch ableiten
        lines = [line.strip() for line in first_page_text.split("\n") if len(line.strip()) > 5]
        cleaned_lines = []
        for line in lines[:12]:
            l_lower = line.lower()
            if not any(stop in l_lower for stop in ["http", "doi.org", "vol.", "issue", "pnas", "www.", "copyright", "downloaded from"]):
                # Banners wie 'RESEARCH ARTICLE | NEUROSCIENCE' entfernen
                clean = re.sub(r"(?i)^(research article|review article|open access|article|report)\s*[|•\-–—]\s*", "", line).strip()
                clean = re.sub(r"(?i)\s*[|•\-–—]\s*(open access|research article|neuroscience)", "", clean).strip()
                if len(clean) > 8:
                    cleaned_lines.append(clean)

        fallback_title = cleaned_lines[0] if cleaned_lines else paper_id.replace("_", " ").title()
        
        # Autoren aus der Zeile unter dem Titel extrahieren (falls vorhanden)
        authors = ["Wissenschaftliche Autoren"]
        if len(cleaned_lines) > 1 and ("," in cleaned_lines[1] or " and " in cleaned_lines[1] or " und " in cleaned_lines[1]):
            raw_authors = re.sub(r"[a-z0-9,]+(?=\s|$)", "", cleaned_lines[1]) # Affiliation markers wie a,b entfernen
            parsed_authors = [re.sub(r"[^a-zA-Z\s\.\-]", "", a).strip() for a in re.split(r"[,;]|\band\b", cleaned_lines[1])]
            filtered_authors = [a for a in parsed_authors if len(a) > 2 and not any(kw in a.lower() for kw in ["edited", "received", "accepted", "university", "department"])]
            if filtered_authors:
                authors = filtered_authors[:8]

        return {
            "title": fallback_title[:150],
            "authors": authors,
            "journal": journal,
            "doi": doi,
            "year": year,
            "summary": first_page_text[:400].strip() + "..."
        }

    def extract_with_llm(self, first_page_text: str, filename: str) -> ExtractedPaperMetadata:
        """Extrahiert präzise Metadaten per Gemini 3.6 Flash (1-Shot structured JSON)."""
        paper_id = Path(filename).stem
        heuristics = self.extract_heuristics(first_page_text, filename)

        if not self.api_key:
            return ExtractedPaperMetadata(
                paper_id=paper_id,
                title=heuristics["title"],
                authors=heuristics["authors"],
                journal=heuristics["journal"],
                published=heuristics["year"],
                doi=heuristics["doi"],
                summary=heuristics["summary"],
                pdf_url=f"https://doi.org/{heuristics['doi']}" if heuristics["doi"] else None
            )

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
  "doi": "DOI falls vorhanden (z.B. 10.1073/pnas.202524065), sonst null",
  "year": "YYYY (z.B. 2024)",
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

            title = data.get("title") or heuristics["title"]
            authors = data.get("authors") or heuristics["authors"]
            journal = data.get("journal") or heuristics["journal"]
            doi = data.get("doi") or heuristics["doi"]
            year = str(data.get("year") or heuristics["year"])
            abstract = data.get("abstract") or heuristics["summary"]

            pdf_url = f"https://doi.org/{doi}" if doi else heuristics.get("pdf_url")

            return ExtractedPaperMetadata(
                paper_id=paper_id,
                title=title,
                authors=authors if isinstance(authors, list) else [str(authors)],
                journal=journal,
                published=year,
                doi=doi,
                summary=abstract,
                pdf_url=pdf_url
            )

        except Exception as e:
            print(f"[MetadataExtractor Info] LLM-Extraktion nicht möglich ({e}). Verwende Heuristiken.")
            return ExtractedPaperMetadata(
                paper_id=paper_id,
                title=heuristics["title"],
                authors=heuristics["authors"],
                journal=heuristics["journal"],
                published=heuristics["year"],
                doi=heuristics["doi"],
                summary=heuristics["summary"],
                pdf_url=f"https://doi.org/{heuristics['doi']}" if heuristics["doi"] else None
            )
