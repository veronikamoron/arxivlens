"""
ArXivLens: Editorial Research Studio (Voize / Warm Sand & Editorial Serif Aesthetic)
Inspiriert vom hochwertigen europäischen MedTech/AI Editorial Design:
Warmer Sandton, edle Serif-Typografie, abgerundete Konturkarten und 100% Free-Tier Garantie.
"""

import os
import time
import streamlit as st
from pathlib import Path

from src.pipeline import ArXivLensPipeline
from src.config import config

# ==============================================================================
# 1. PAGE CONFIG & EDITORIAL WARM SAND CSS
# ==============================================================================
st.set_page_config(
    page_title="ArXivLens | Editorial Research Studio",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Google Fonts: Editorial Serif + Modern Clean Sans */
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    /* Global Body & Viewport (Warm Sand & Charcoal) */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FAF7F2 !important;
        color: #1E293B !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    [data-testid="stHeader"] {
        background-color: rgba(250, 247, 242, 0.85) !important;
        backdrop-filter: blur(12px) !important;
    }

    [data-testid="stSidebar"] {
        background-color: #F3EFE6 !important;
        border-right: 1.5px solid #E2DCD0 !important;
    }

    /* Headings (Editorial Serif) */
    h1, h2, h3, .serif-font {
        font-family: 'Newsreader', Georgia, serif !important;
        color: #0F172A !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    /* Editorial Overline */
    .editorial-overline {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.20em;
        text-transform: uppercase;
        color: #64748B;
        margin-bottom: 8px;
    }

    /* Top Disclaimer Banner */
    .studio-disclaimer {
        background-color: #FFFFFF;
        border: 1.5px solid #E2DCD0;
        border-radius: 12px;
        padding: 10px 18px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.84rem;
        color: #475569;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .disclaimer-badge {
        background-color: #0F172A;
        color: #FAF7F2;
        font-weight: 700;
        font-size: 0.68rem;
        padding: 3px 8px;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-right: 10px;
    }

    /* Hero Section (Voize Style) */
    .hero-split-container {
        display: flex;
        gap: 24px;
        margin-bottom: 28px;
    }
    .hero-left-box {
        flex: 1.1;
        padding: 10px 0;
    }
    .hero-main-title {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 2.35rem;
        font-weight: 600;
        line-height: 1.15;
        color: #0F172A;
        margin-bottom: 14px;
        letter-spacing: -0.03em;
    }
    .hero-subtext {
        font-size: 0.98rem;
        line-height: 1.6;
        color: #475569;
        max-width: 95%;
    }

    /* Rounded Editorial Cards (Layered Box Look) */
    .editorial-card {
        background-color: #FFFFFF;
        border: 1.5px solid #0F172A;
        border-radius: 20px;
        padding: 22px 26px;
        margin-bottom: 14px;
        box-shadow: 4px 4px 0px rgba(15, 23, 42, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .editorial-card:hover {
        transform: translateY(-2px);
        box-shadow: 4px 6px 0px rgba(15, 23, 42, 0.09);
    }
    .editorial-card-title {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 6px;
    }
    .editorial-card-desc {
        font-size: 0.86rem;
        line-height: 1.5;
        color: #64748B;
    }

    /* Paper Canvas (Voize Large Container) */
    .paper-canvas-editorial {
        background-color: #FFFFFF;
        border: 1.8px solid #0F172A;
        border-radius: 22px;
        padding: 26px 30px;
        margin-bottom: 26px;
        box-shadow: 4px 6px 0px rgba(15, 23, 42, 0.05);
    }
    .paper-canvas-heading {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.65rem;
        font-weight: 600;
        color: #0F172A;
        line-height: 1.25;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }
    .author-pill {
        display: inline-block;
        background-color: #F4EFE6;
        color: #1E293B;
        border: 1px solid #D8CFC0;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.80rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
    }
    .canvas-metrics-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 16px;
        padding-top: 14px;
        border-top: 1.5px solid #F1EAE0;
    }
    .metric-badge {
        background-color: #FAF7F2;
        border: 1px solid #E2DCD0;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #334155;
    }

    /* Peer-Review Citation Cards */
    .citation-editorial-card {
        background-color: #FFFFFF;
        border: 1.5px solid #0F172A;
        border-radius: 16px;
        padding: 16px 20px;
        margin-top: 12px;
        margin-bottom: 12px;
        box-shadow: 2px 3px 0px rgba(15, 23, 42, 0.05);
    }
    .citation-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .citation-section-badge {
        background-color: #0F172A;
        color: #FAF7F2;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .citation-score-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        font-weight: 700;
        color: #0F172A;
        background-color: #E2E8F0;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .citation-quote-box {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.88rem;
        line-height: 1.55;
        color: #334155;
        background-color: #FAF7F2;
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 3px solid #0F172A;
        margin-top: 6px;
    }

    /* Telemetry Pill */
    .telemetry-pill-light {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.78rem;
        color: #475569;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .telemetry-bold {
        color: #0F172A;
        font-weight: 700;
    }

    /* Buttons Styling */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #0F172A !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 8px 18px !important;
        box-shadow: 2px 2px 0px rgba(15, 23, 42, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background-color: #0F172A !important;
        color: #FAF7F2 !important;
        border-color: #0F172A !important;
        box-shadow: 2px 4px 0px rgba(15, 23, 42, 0.15) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #0F172A !important;
        color: #FAF7F2 !important;
        border: 1.5px solid #0F172A !important;
        box-shadow: 3px 3px 0px rgba(15, 23, 42, 0.12) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1.5px solid #E2DCD0;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #64748B;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #0F172A !important;
        border-bottom: 2.5px solid #0F172A !important;
        font-weight: 700 !important;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2DCD0 !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. SESSION STATE MANAGEMENT
# ==============================================================================
if "pipeline" not in st.session_state:
    st.session_state.pipeline = ArXivLensPipeline()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_paper_id" not in st.session_state:
    st.session_state.active_paper_id = None

if "last_retrieved_chunks" not in st.session_state:
    st.session_state.last_retrieved_chunks = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ==============================================================================
# 3. HELPER: BIBTEX GENERATOR
# ==============================================================================
def generate_bibtex(metadata: dict) -> str:
    """Generiert einen formellen akademischen BibTeX-Eintrag."""
    paper_id = metadata.get("arxiv_id", "paper")
    authors = metadata.get("authors", ["Unknown"])
    first_author = authors[0].split()[-1].lower() if authors else "author"
    year = metadata.get("published", "2024")[:4]
    key = f"{first_author}{year}{paper_id.replace('.', '')}"
    author_str = " and ".join(authors)
    return f"""@article{{{key},
  author    = {{{author_str}}},
  title     = {{{metadata.get('title', 'Unknown Title')}}},
  journal   = {{arXiv preprint arXiv:{paper_id}}},
  year      = {{{year}}},
  url       = {{{metadata.get('pdf_url', 'https://arxiv.org/abs/' + paper_id)}}}
}}"""

# ==============================================================================
# 4. SIDEBAR: GOOGLE KEY & FREE-TIER SCHUTZ
# ==============================================================================
with st.sidebar:
    st.markdown("<div class='editorial-overline'>P O R T F O L I O · D E M O</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-family: Newsreader, Georgia, serif; font-size: 1.5rem; margin-top: -6px;'>ArXivLens Studio</h2>", unsafe_allow_html=True)
    st.caption("Editorial Research & Information Retrieval Engine")

    st.markdown("---")
    st.markdown("#### 🔑 Google Gemini API Key")
    
    default_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API-Key (Free Tier)",
        value=default_key,
        type="password",
        help="Kostenlos auf https://aistudio.google.com/ generieren (0,00 € dauerhaft)",
        placeholder="AIzaSy..."
    )

    if api_key_input:
        st.session_state.pipeline.update_api_key(api_key_input)
        st.success("API Key verifiziert!", icon="✅")
        st.caption("🔒 **100% Free-Tier Garantie:** Strikte Beschränkung auf `embedding-001` & `gemini-3.6-flash`. Garantiert null Kosten.")
    else:
        st.warning("Google API-Key eintragen, um Anfragen zu starten.", icon="⚠️")

    st.markdown("---")
    st.markdown("#### ⚙️ Retrieval-Konfiguration")
    use_reranker = st.toggle("✨ FlashRank Cross-Encoder", value=True, help="Sortiert Chunks mit einem lokalen CPU-Cross-Encoder neu für maximale Präzision.")

    if st.button("🔄 Pipeline zurücksetzen", use_container_width=True):
        st.session_state.pipeline = ArXivLensPipeline()
        st.session_state.last_retrieved_chunks = []
        st.success("Pipeline neu initialisiert!")
        st.rerun()

    st.markdown("---")
    st.markdown("#### ⚖️ Academic Disclaimer")
    with st.expander("Forschungs- & Portfolio-Hinweis", expanded=False):
        st.markdown("""
        **Academic Demo & Portfolio Project:**  
        - Entwickelt für Demonstrations-, Bildungs- und Forschungszwecke im Rahmen eines Developer-Portfolios.
        - Antworten basieren auf KI-Modellen und können Ungenauigkeiten enthalten.
        - Es findet keine dauerhafte Speicherung personenbezogener Daten statt.
        """)

# ==============================================================================
# 5. TOP DISCLAIMER BANNER
# ==============================================================================
st.markdown("""
<div class="studio-disclaimer">
    <div>
        <span class="disclaimer-badge">Portfolio Demo</span>
        <span>Wissenschaftliches RAG-System zu Demonstrationszwecken. Betrieben mit Google Gemini 3.6 Flash & 100% Free Tier.</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 6. HERO SECTION (VOIZE-INSPIRIERTER EDITORIAL LOOK)
# ==============================================================================
st.markdown("""
<div class="hero-split-container">
    <div class="hero-left-box">
        <div class="editorial-overline">F O R S C H U N G S A S S I S T E N T</div>
        <div class="hero-main-title">Aktive Entlastung im Moment der Paper-Analyse</div>
        <div class="hero-subtext">
            Mit Section-Aware Chunking, Hybrid BM25 Keyword Search und lokalem FlashRank Cross-Encoder werden wissenschaftliche Arbeiten strukturiert erschlossen – vollständig transparent und zu 100% kostenlos im Google Free Tier.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Zweispaltige visuelle Highlight-Karten (wie im Bild)
card_col1, card_col2 = st.columns(2)
with card_col1:
    st.markdown("""
    <div class="editorial-card">
        <div class="editorial-card-title">Mehr Zeit für echte Erkenntnisse</div>
        <div class="editorial-card-desc">
            Keine manuelle Volltext-Suche durch hunderte Seiten. Hybrid Retrieval findet Formeln, Modell-Architekturen und spezifische Benchmarks in Millisekunden.
        </div>
    </div>
    """, unsafe_allow_html=True)

with card_col2:
    st.markdown("""
    <div class="editorial-card">
        <div class="editorial-card-title">Keine Angst vor Halluzinationen</div>
        <div class="editorial-card-desc">
            Jede Aussage wird durch verifizierte Beleg-Karten mit exakter Seitenzahl und Re-Ranking-Score gestützt. Unbelegte Fakten werden strikt abgewiesen.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 7. PAPER INGESTION & ONBOARDING
# ==============================================================================
st.markdown("<div class='editorial-overline'>D O K U M E N T E N - A U S W A H L</div>", unsafe_allow_html=True)
st.markdown("<h3 style='margin-top: -6px;'>Wähle eine Forschungsarbeit zum Analysieren</h3>", unsafe_allow_html=True)

ingest_col1, ingest_col2 = st.columns([1.3, 1])

with ingest_col1:
    st.markdown("**1-Klick Meilenstein-Arbeiten:**")
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("📄 Attention Is All You Need", use_container_width=True, help="Transformer Architektur (1706.03762)"):
            with st.spinner("Lade Transformer-Paper herunter und berechne Embeddings..."):
                try:
                    res = st.session_state.pipeline.ingest_arxiv_paper("1706.03762")
                    st.session_state.active_paper_id = res["paper_id"]
                    st.success(f"Indiziert: {res['title']} ({res['chunk_count']} Chunks)", icon="✅")
                except Exception as e:
                    st.error(f"Fehler: {e}")

    with btn2:
        if st.button("📄 Retrieval-Augmented Generation", use_container_width=True, help="Original RAG Paper von Lewis et al. (2005.11401)"):
            with st.spinner("Lade RAG-Paper herunter und berechne Embeddings..."):
                try:
                    res = st.session_state.pipeline.ingest_arxiv_paper("2005.11401")
                    st.session_state.active_paper_id = res["paper_id"]
                    st.success(f"Indiziert: {res['title']} ({res['chunk_count']} Chunks)", icon="✅")
                except Exception as e:
                    st.error(f"Fehler: {e}")

with ingest_col2:
    st.markdown("**Eigenes Paper importieren:**")
    tab_arxiv, tab_upload = st.tabs(["ArXiv ID / URL", "Lokale PDF"])
    
    with tab_arxiv:
        arxiv_id_input = st.text_input("ArXiv ID:", placeholder="z.B. 2310.06825", label_visibility="collapsed")
        if st.button("Von ArXiv abrufen", use_container_width=True):
            if arxiv_id_input:
                with st.spinner(f"Lade ArXiv-Paper '{arxiv_id_input}' herunter..."):
                    try:
                        res = st.session_state.pipeline.ingest_arxiv_paper(arxiv_id_input)
                        st.session_state.active_paper_id = res["paper_id"]
                        st.success(f"Indiziert: {res['title']} ({res['chunk_count']} Chunks)", icon="✅")
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    with tab_upload:
        uploaded_file = st.file_uploader("PDF hochladen:", type=["pdf"], label_visibility="collapsed")
        if uploaded_file and st.button("PDF parsen & indizieren", use_container_width=True):
            temp_dir = Path("./data/uploads")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner(f"Verarbeite '{uploaded_file.name}'..."):
                try:
                    res = st.session_state.pipeline.ingest_uploaded_pdf(str(temp_path), uploaded_file.name)
                    st.session_state.active_paper_id = res["arxiv_id"]
                    st.success(f"Indiziert: {res['title']} ({res['chunk_count']} Chunks)", icon="✅")
                except Exception as e:
                    st.error(f"Fehler: {e}")

# ==============================================================================
# 8. INTERAKTIVE PAPER-CANVAS (GROSSE EDITORIAL CARD)
# ==============================================================================
indexed = st.session_state.pipeline.indexed_papers
if indexed:
    paper_options = {pid: f"{meta['title']} ({pid})" for pid, meta in indexed.items()}
    selected_pid = st.selectbox(
        "Aktives Arbeitsdokument:",
        options=list(paper_options.keys()),
        format_func=lambda x: paper_options[x],
        index=list(paper_options.keys()).index(st.session_state.active_paper_id) if st.session_state.active_paper_id in paper_options else 0
    )
    st.session_state.active_paper_id = selected_pid

    current_meta = indexed.get(st.session_state.active_paper_id, {})
    authors = current_meta.get("authors", [])
    author_pills_html = "".join([f"<span class='author-pill'>{a}</span>" for a in authors[:5]])
    if len(authors) > 5:
        author_pills_html += f"<span class='author-pill'>+{len(authors)-5} weitere</span>"

    st.markdown(f"""
    <div class="paper-canvas-editorial">
        <div class="editorial-overline">A K T I V E S  D O K U M E N T</div>
        <div class="paper-canvas-heading">{current_meta.get('title', 'Unbekanntes Dokument')}</div>
        <div>{author_pills_html}</div>
        <div class="canvas-metrics-row">
            <span class="metric-badge">📄 {current_meta.get('chunk_count', 0)} Chunks extrahiert</span>
            <span class="metric-badge">🔍 Hybrid BM25 + Dense Index</span>
            <span class="metric-badge">⚡ Google Gemini 3.6 Flash</span>
            <span class="metric-badge">📅 {current_meta.get('published', '2024')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 BibTeX Zitation generieren / kopieren", expanded=False):
        st.code(generate_bibtex(current_meta), language="bibtex")

st.markdown("---")

# ==============================================================================
# 9. 3-TAB DASHBOARD: CHAT, EVIDENCE INSPECTOR & SUMMARY
# ==============================================================================
tab_chat, tab_evidence, tab_summary = st.tabs([
    "💬 Peer-Review Q&A",
    "🔍 Belege & Telemetrie",
    "📑 1-Klick Paper Summary"
])

# ------------------------------------------------------------------------------
# TAB 1: CHAT & SMART SUGGESTION CHIPS
# ------------------------------------------------------------------------------
with tab_chat:
    if not st.session_state.active_paper_id:
        st.info("💡 Wähle oben ein Paper aus, um die interaktive Q&A-Session zu starten.")
    else:
        st.markdown("<div class='editorial-overline'>V O R S C H L Ä G E</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.9rem; font-weight: 600; color: #334155; margin-bottom: 8px;'>Häufige Forschungsfragen (1-Klick Vorschau):</div>", unsafe_allow_html=True)
        
        # Vorschläge nach Paper
        if "1706.03762" in st.session_state.active_paper_id:
            suggestions = [
                "📐 Wie berechnet sich die Scaled Dot-Product Attention?",
                "📊 Welchen BLEU-Score erreicht das Big Transformer Modell auf WMT?",
                "🖥️ Welche Hardware und Trainingszeit wurde verwendet?"
            ]
        elif "2005.11401" in st.session_state.active_paper_id:
            suggestions = [
                "🧠 Was unterscheidet parametrisches und nicht-parametrisches Gedächtnis?",
                "📈 Wie schneidet RAG im Vergleich zu T5 und REALM ab?",
                "🔍 Welche Vektordatenbank und welcher Retriever wird verwendet?"
            ]
        else:
            suggestions = [
                "🎯 Was ist das Kernproblem und die primäre Innovation des Papers?",
                "🔬 Wie funktioniert die Methodik und die Systemarchitektur?",
                "📊 Welche experimentellen Hauptergebnisse und Benchmarks werden genannt?"
            ]

        chip_c1, chip_c2, chip_c3 = st.columns(3)
        with chip_c1:
            if st.button(suggestions[0], use_container_width=True):
                st.session_state.pending_query = suggestions[0]
        with chip_c2:
            if st.button(suggestions[1], use_container_width=True):
                st.session_state.pending_query = suggestions[1]
        with chip_c3:
            if st.button(suggestions[2], use_container_width=True):
                st.session_state.pending_query = suggestions[2]

        st.markdown("<br>", unsafe_allow_html=True)

        # Bisherige Chat-Nachrichten anzeigen
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Telemetrie-Zeile falls vorhanden
                if "telemetry" in msg:
                    t = msg["telemetry"]
                    st.markdown(f"""
                    <div class="telemetry-pill-light">
                        <span>⚡ <span class="telemetry-bold">Gemini 3.6 Flash</span></span>
                        <span>⏱️ <span class="telemetry-bold">{t['latency']:.0f} ms</span></span>
                        <span>📚 <span class="telemetry-bold">{t['chunks_count']} Belege verifiziert</span></span>
                    </div>
                    """, unsafe_allow_html=True)

                # Peer-Review Citation Cards
                if "chunks" in msg and msg["chunks"]:
                    with st.expander(f"📚 Verifizierte Belege ({len(msg['chunks'])})", expanded=False):
                        for idx, chunk in enumerate(msg["chunks"], start=1):
                            score_label = f"Match: {chunk.rerank_score*100:.1f}%" if chunk.rerank_score is not None else f"RRF: {chunk.rrf_score:.4f}"
                            st.markdown(f"""
                            <div class="citation-editorial-card">
                                <div class="citation-header-row">
                                    <span class="citation-section-badge">[Beleg {idx}] {chunk.section} (Seite {chunk.page_number})</span>
                                    <span class="citation-score-tag">{score_label}</span>
                                </div>
                                <div class="citation-quote-box">{chunk.text}</div>
                            </div>
                            """, unsafe_allow_html=True)

        # Eingabe verarbeiten
        chat_input_query = st.chat_input("Frage zum Paper stellen (z.B. Formeln, Benchmarks, Methodik)...")
        active_query = st.session_state.pending_query or chat_input_query
        st.session_state.pending_query = None

        if active_query:
            if not api_key_input:
                st.error("Bitte trage zuerst deinen kostenlosen Google API-Key in der linken Sidebar ein.")
            else:
                # Nutzernachricht speichern
                st.session_state.messages.append({"role": "user", "content": active_query})
                with st.chat_message("user"):
                    st.markdown(active_query)

                # Antwort streamen & Latenz messen
                with st.chat_message("assistant"):
                    t_start = time.perf_counter()
                    with st.spinner("Hybrid Search & Cross-Encoder aktiv..."):
                        try:
                            stream_gen, retrieved_chunks = st.session_state.pipeline.ask_stream(
                                query=active_query,
                                paper_id=st.session_state.active_paper_id,
                                use_reranker=use_reranker
                            )
                            st.session_state.last_retrieved_chunks = retrieved_chunks

                            # Live-Streaming
                            response_text = st.write_stream(stream_gen)
                            latency_ms = (time.perf_counter() - t_start) * 1000

                            telemetry_data = {
                                "latency": latency_ms,
                                "chunks_count": len(retrieved_chunks)
                            }
                            st.markdown(f"""
                            <div class="telemetry-pill-light">
                                <span>⚡ <span class="telemetry-bold">Gemini 3.6 Flash</span></span>
                                <span>⏱️ <span class="telemetry-bold">{latency_ms:.0f} ms</span></span>
                                <span>📚 <span class="telemetry-bold">{len(retrieved_chunks)} Belege verifiziert</span></span>
                            </div>
                            """, unsafe_allow_html=True)

                            # Peer-Review Citation Cards
                            if retrieved_chunks:
                                with st.expander(f"📚 Verifizierte Belege ({len(retrieved_chunks)})", expanded=True):
                                    for idx, chunk in enumerate(retrieved_chunks, start=1):
                                        score_label = f"Match: {chunk.rerank_score*100:.1f}%" if chunk.rerank_score is not None else f"RRF: {chunk.rrf_score:.4f}"
                                        st.markdown(f"""
                                        <div class="citation-editorial-card">
                                            <div class="citation-header-row">
                                                <span class="citation-section-badge">[Beleg {idx}] {chunk.section} (Seite {chunk.page_number})</span>
                                                <span class="citation-score-tag">{score_label}</span>
                                            </div>
                                            <div class="citation-quote-box">{chunk.text}</div>
                                        </div>
                                        """, unsafe_allow_html=True)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_text,
                                "chunks": retrieved_chunks,
                                "telemetry": telemetry_data
                            })
                        except Exception as e:
                            st.error(f"Fehler bei der Antwortgenerierung: {e}")

# ------------------------------------------------------------------------------
# TAB 2: EVIDENCE & TELEMETRIE
# ------------------------------------------------------------------------------
with tab_evidence:
    st.markdown("<div class='editorial-overline'>A N A L Y S E</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: -6px;'>Information-Retrieval & Cross-Encoder Deep-Dive</h3>", unsafe_allow_html=True)
    st.caption("Vergleichende Analyse: Wie bewerten Vektorsuche, BM25 und FlashRank die extrahierten Abschnitte?")

    chunks_to_inspect = st.session_state.last_retrieved_chunks
    if not chunks_to_inspect:
        st.info("💡 Stelle zuerst eine Frage im Chat, um die mathematische Trefferanalyse hier einzusehen.")
    else:
        for idx, chunk in enumerate(chunks_to_inspect, start=1):
            with st.container():
                st.markdown(f"#### Beleg #{idx}: {chunk.section} *(Seite {chunk.page_number})*")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("FlashRank Match", f"{chunk.rerank_score*100:.1f} %" if chunk.rerank_score is not None else "N/A")
                with col2:
                    st.metric("RRF Score", f"{chunk.rrf_score:.4f}")
                with col3:
                    st.metric("Dense Sim", f"{chunk.dense_score:.4f}" if chunk.dense_score is not None else "N/A")
                with col4:
                    st.metric("BM25 Keyword", f"{chunk.bm25_score:.2f}" if chunk.bm25_score is not None else "N/A")

                st.markdown(f"""
                <div class="citation-quote-box" style="margin-top: 8px;">
                    {chunk.text}
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

# ------------------------------------------------------------------------------
# TAB 3: 1-KLICK PAPER SUMMARY
# ------------------------------------------------------------------------------
with tab_summary:
    st.markdown("<div class='editorial-overline'>Z U S A M M E N F A S S U N G</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: -6px;'>Akademische Executive Summary</h3>", unsafe_allow_html=True)
    st.caption("Generiert auf Knopfdruck eine strukturierte Analyse des gesamten Papers.")

    if not st.session_state.active_paper_id:
        st.info("Bitte wähle oben ein Paper aus.")
    else:
        if st.button("🚀 Executive Summary jetzt erstellen", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("Bitte Google API-Key in der Sidebar eintragen.")
            else:
                with st.spinner("Analysiere Architektur, Innovationen und Benchmarks mit Gemini 3.6 Flash..."):
                    try:
                        summary_text = st.session_state.pipeline.generate_summary(st.session_state.active_paper_id)
                        st.markdown(summary_text)
                    except Exception as e:
                        st.error(f"Fehler: {e}")
