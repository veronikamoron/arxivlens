"""
Prompt-Templates für akademische Q&A, Zitations-Grounding und 1-Klick Zusammenfassungen.
"""

from typing import List
from ..retrieval.hybrid import SearchResult

class PromptTemplates:
    """Verwaltet System- und User-Prompts für wissenschaftliche RAG-Generierung."""

    SYSTEM_PROMPT = """Du bist 'ArXivLens', ein hochentwickelter KI-Forschungsassistent für wissenschaftliche Arbeiten.
Deine Aufgabe ist es, Fragen zu den bereitgestellten wissenschaftlichen Arbeiten präzise, faktenbasiert und akademisch fundiert zu beantworten.

WICHTIGE REGELN FÜR DIE ANTWORT:
1. ZITIERE IMMER DIE QUELLE: Verwende Inline-Zitate wie [Quelle 1 (S. X)] oder [Quelle 2 (S. Y)], wann immer du eine Aussage triffst.
2. STRIKTE FAKTIENTREUE: Erfinde KEINE Zahlen, Benchmarks oder Formeln. Nutze ausschließlich die im Kontext genannten Informationen.
3. WISSENSLÜCKEN EINGESTEHEN: Wenn der bereitgestellte Kontext die Frage nicht beantwortet, sage klar: "Auf Basis der vorliegenden Textauszüge des Papers kann diese Frage nicht eindeutig beantwortet werden."
4. STRUKTUR: Antworte klar gegliedert (Bulletpoints, prägnante Absätze, bei Vergleichen gerne kurze Markdown-Tabellen).
5. SPRACHE: Antworte standardmäßig auf Deutsch (Fachbegriffe wie 'Self-Attention', 'Transformer', 'BLEU Score' im englischen Original belassen).
"""

    @staticmethod
    def build_qa_prompt(query: str, context_chunks: List[SearchResult]) -> str:
        """Baut den Prompt für die Frage-Antwort-Generierung mit Kontext-Chunks auf."""
        context_str = ""
        for idx, chunk in enumerate(context_chunks, start=1):
            score_info = f"Re-Rank: {chunk.rerank_score}" if chunk.rerank_score is not None else f"RRF: {chunk.rrf_score}"
            context_str += f"""
--- QUELLE {idx} ---
Titel: {chunk.title}
Abschnitt: {chunk.section} (Seite {chunk.page_number})
Score: {score_info}
Auszug:
{chunk.text}
"""

        user_prompt = f"""Hier ist der relevante Kontext aus den wissenschaftlichen Arbeiten:
{context_str}

----------------
FRAGE DES NUTZERS:
{query}

Bitte beantworte die Frage ausführlich und fundiert. Belege jede Kernaussage mit der entsprechenden Quellenangabe (z.B. [Quelle 1 (S. {context_chunks[0].page_number if context_chunks else 1})]).
"""
        return user_prompt

    @staticmethod
    def build_summary_prompt(paper_title: str, abstract: str, key_chunks: List[SearchResult]) -> str:
        """Baut einen Prompt für eine 1-Klick Executive Summary des Papers."""
        context_str = "\n\n".join([f"[{c.section}, S. {c.page_number}]: {c.text}" for c in key_chunks[:6]])
        return f"""Bitte erstelle eine strukturierte, akademische Zusammenfassung des folgenden Papers:

TITEL: {paper_title}
ABSTRACT: {abstract}

WEITERE KERNAUSZÜGE AUS METHODIK & EXPERIMENTEN:
{context_str}

GLIEDERE DEINE ZUSAMMENFASSUNG IN DIESE 4 PUNKTE:
1. 🎯 Kernproblem & Innovation (Was löst das Paper, was vorher nicht möglich war?)
2. 🔬 Methodik & Architektur (Wie funktioniert der vorgeschlagene Ansatz technisch?)
3. 📊 Wichtigste Benchmarks & Ergebnisse (Konkrete Zahlen, Datensätze, Metriken)
4. ⚠️ Limitationen & Ausblick (Welche Schwachstellen oder offenen Fragen gibt es?)
"""
