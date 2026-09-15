# 🔬 ArXivLens: Academic Research Studio & Paper Synthesis RAG

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit%20Academic%20Studio-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini API](https://img.shields.io/badge/LLM-Gemini%203.6%20Flash%20(Free%20Tier)-8E75B2.svg)](https://aistudio.google.com/)
[![Vector Store](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Re-Ranking](https://img.shields.io/badge/Re--Ranker-FlashRank%20(CPU)-green.svg)](https://github.com/PrithivirajDamodaran/FlashRank)


> **Ein praxisnahes, kostenloses RAG-System für wissenschaftliche Arbeiten, das reale Probleme wie zerschnittene Tabellen, Formelverluste und ungenaue Zitate durch hybride Suche und Cross-Encoder Re-Ranking löst.**

---

## 💡 Warum dieses Projekt existiert (Das Problem mit Standard-RAG)

Fast jedes RAG-Tutorial im Internet nutzt dasselbe naive Rezept:
`PDF laden → 500 Zeichen Splitter → Embeddings → Cosine Similarity → Prompt`.

Wer das jemals mit einem echten ArXiv-Paper (wie *„Attention Is All You Need“*) ausprobiert hat, weiß, wie schnell das scheitert:
1. **Zerschnittene Tabellen & Formeln:** Ein starrer Zeichen-Splitter schneidet mathematische Gleichungen oder Benchmark-Ergebnisse mitten im Satz ab.
2. **Bibliografie-Müll:** Bis zu 30 % des Vektorspeichers wird durch Literaturverzeichnisse (`References`) verschwendet. Fragt man nach Autoren, zitiert das System frühere Quellen statt die tatsächliche Studie.
3. **Begriffsblindheit von Embeddings:** Reines Cosine-Similarity-Matching versagt häufig bei spezifischen Bezeichnungen (z.B. *„BLEU-4 Score“*, *„LoRA r=16“* oder *„Table 3“*), weil solche Begriffe im semantischen Vektorraum untergehen.

**ArXivLens wurde gebaut, um genau diese Schwachstellen mit modernen Information-Retrieval-Techniken systematisch zu beheben.**

---

## 🏗️ Architektur & Pipeline

```mermaid
graph TD
    subgraph "1. Ingestion & Section-Aware Parsing"
        A[ArXiv ID / PDF Upload] --> B[PyPDF Reader]
        B --> C[Section Detector: Abstract, Method, Results]
        C -->|Filtert Literaturverzeichnis heraus| D[Saubere Chunks mit Metadaten]
    end

    subgraph "2. Dual-Indexierung"
        D --> E1[Google text-embedding-004]
        D --> E2[BM25 Okapi Tokenizer]
        E1 --> F1[(ChromaDB Local)]
        E2 --> F2[(BM25 In-Memory Index)]
    end

    subgraph "3. Hybrid Retrieval & Re-Ranking"
        Q[User Query] --> G1[Dense Semantic Search]
        Q --> G2[Sparse Keyword Search]
        F1 --> G1
        F2 --> G2
        G1 & G2 --> H[Reciprocal Rank Fusion - RRF]
        H -->|Top 12 Kandidaten| I[FlashRank Cross-Encoder]
        I -->|Top 4 Präzise Chunks| J[Grounding & Context Injection]
    end

    subgraph "4. Antwortgenerierung & UI"
        J --> K[Google Gemini 2.0 Flash]
        K -->|Streaming mit Inline-Zitaten| L[Streamlit 3-Tab Dashboard]
    end
```

---

## ⚡ Die Kern-Features im Überblick

### 1. Section-Aware Markdown Parsing
Statt blind nach Zeichenanzahl zu schneiden, erkennt der Parser typische wissenschaftliche Abschnitte (*Abstract, Model Architecture, Experiments, Discussion*). Sobald die *References* beginnen, stoppt die Indizierung – das hält den Index sauber und spart Token.

### 2. Hybrid Search (Dense + BM25 via Reciprocal Rank Fusion)
- **Dense Embeddings (Google text-embedding-004):** Findet konzeptionelle Zusammenhänge (*„Wie skaliert der Attention-Mechanismus mit der Sequenzlänge?“*).
- **Sparse BM25 Search:** Fängt exakte Begriffe, Tabellenbezeichnungen und Metriken ab (*„BLEU Score WMT 2014“*).
- **RRF:** Kombiniert beide Ranglisten über die Formel:
  $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{1}{k + \text{rank}_m(d)}$$

### 3. FlashRank Re-Ranking (Lokaler Cross-Encoder)
Anstatt alle Chunks ungefiltert an das LLM zu schicken, analysiert FlashRank (Cross-Encoder auf CPU) jedes Query-Chunk-Paar gemeinsam. Im UI gibt es einen Live-Schalter, mit dem Tester den Effekt *(„Mit vs. Ohne Re-Ranking“)* direkt nachvollziehen können.

### 4. 0,00 € Betriebskosten & BYOK-Modell
- Läuft vollständig über den dauerhaft kostenlosen **Google Gemini Free Tier** (keine Kreditkarte erforderlich).
- **Dual-Input:** Für Entwickler direkt via `.env`, für fremde Tester über ein Passwort-Feld in der Streamlit-Sidebar.

---

## 🖥️ Das Web-Dashboard: Editorial Research Studio

Vergiss sterile, seelenlose KI-Chatfenster. Das Interface von ArXivLens wurde als **warmes, fokussiertes Editorial Studio** konzipiert – inspiriert von modernstem europäischen Produkt- und Magazin-Design:

* 🎨 **Warme Sand- & Serif-Ästhetik:** Sanfter Elfenbeinton (`#FAF7F2`) kombiniert mit ausdrucksstarker Buchdruck-Typografie (*Newsreader*) und markanten Konturkarten (`1.5px solid #0F172A`). Liest sich wie ein hochwertiges Forschungsmagazin und schont die Augen bei stundenlanger Recherche.
* 📑 **Interaktive Paper-Canvas:** Zeigt geladene Dokumente mit Autoren-Pills, RAG-Metadaten und einem integrierten **BibTeX-Generator** für sofortiges wissenschaftliches Zitieren.
* 💡 **Smart Suggestion Chips (1-Klick Einstieg):** Direkt über dem Chatfeld schlägt das System die 3 wichtigsten Fachfragen zum aktiven Paper vor (z.B. *„📐 Wie berechnet sich die Scaled Dot-Product Attention?“* oder *„📊 Welcher BLEU-Score wurde erzielt?“*).
* 💬 **Tab 1: Peer-Review Q&A:** Fließende Streaming-Antworten mit nummerierten Inline-Zitaten. Jede Antwort enthält aufklappbare Beleg-Karten mit Original-Textauszug und Cross-Encoder Match-Score.
* 🔍 **Tab 2: Evidence & Telemetrie:** Volle Transparenz unter der Haube: Vergleiche Dense Semantic Similarity, BM25 Keyword-Score und FlashRank Re-Ranking Werte direkt nebeneinander.
* ⚡ **Tab 3: 1-Klick Executive Summary:** Generiert auf Knopfdruck eine strukturierte Analyse des gesamten Papers (Kerninnovation, Architektur, Benchmarks und Limitationen).
* ⏱️ **Echtzeit-Telemetrie:** Jede Antwort zeigt transparent Latenz und Verifizierungsgrad (`⚡ Gemini 3.6 Flash · ⏱️ 420 ms · 📚 4 Belege verifiziert`).


---

## 🛡️ Sicherheits- & Datenschutzkonzept (Zero-Leakage Guarantee)

Dieses Repository ist für ein öffentliches Portfolio optimiert, schützt aber alle privaten Testdaten und Keys kompromisslos über die `.gitignore`:
- 🚫 **Keine API-Keys im Git-Verlauf:** `.env` und `.streamlit/secrets.toml` sind strikt ignoriert.
- 🚫 **Keine Vektor-Dumps:** Lokale ChromaDB-Dateien (`chroma_db/`) verbleiben ausschließlich lokal.
- 🚫 **Keine privaten PDFs:** Heruntergeladene und hochgeladene PDFs werden nicht committed.

---

## 🚀 Schnelleinstieg & Lokale Ausführung

### 1. Repository klonen & Umgebung erstellen
```bash
git clone https://github.com/dein-username/arxivlens.git
cd arxivlens

# Virtuelle Umgebung anlegen
python -m venv .venv
source .venv/bin/activate  # Unter Windows: .venv\Scripts\activate
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. API-Key konfigurieren (Optional, da auch im UI eingebbar)
Kopiere die Vorlage und trage deinen kostenlosen Gemini-Key ein ([Hier kostenlos generieren](https://aistudio.google.com/)):
```bash
cp .env.example .env
```

### 4. Streamlit Dashboard starten
```bash
streamlit run app.py
```
Die Weboberfläche öffnet sich automatisch unter `http://localhost:8501`.

---

## 🧪 Tests & Benchmarks

Das Projekt enthält eine vollständige Pytest-Suite, die **100 % offline und ohne API-Key in weniger als 2 Sekunden durchläuft**:

```bash
# Unit-Tests ausführen
pytest tests/ -v
```

Um die Retrieval-Latenz und den Re-Ranking-Score-Gewinn auf einem synthetischen wissenschaftlichen Korpus zu testen:
```bash
python evaluate.py
```

Beispiel-Output des Benchmark-Skripts:
```text
=================================================================
🔬 ARXIVLENS: RETRIEVAL & RE-RANKING BENCHMARK REPORT
=================================================================
[✓] Indexierung abgeschlossen in 1.42 ms

Evaluierung der Testanfragen:
-----------------------------------------------------------------
Query                               | BM25 Hit   | Re-Rank Score
-----------------------------------------------------------------
What BLEU score did the transform...| PASS       | 0.9842      
How is the scaled dot-product att...| PASS       | 0.9615      
What is the difference between pa...| PASS       | 0.9901      
-----------------------------------------------------------------
📊 Durchschnittliche Pipeline-Latenz (BM25 + FlashRank): 14.8 ms
=================================================================
```

---

## ⚖️ Haftungsausschluss / Disclaimer

> [!NOTE]
> **Educational & Research Portfolio Project:** Dieses Projekt dient ausschließlich zu Demonstrations-, Bildungs- und Evaluierungszwecken im Rahmen eines Entwickler-Portfolios. Generierte LLM-Inhalte können Ungenauigkeiten enthalten.
