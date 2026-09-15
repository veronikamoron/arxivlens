"""
Zentrale Konfiguration für ArXivLens.
Lädt Umgebungsvariablen aus der .env-Datei mit sicheren Standardwerten.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Lädt .env falls vorhanden (ohne Fehler, wenn keine .env existiert)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class AppConfig(BaseModel):
    # Google Gemini API Konfiguration
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "models/embedding-001"))


    
    # Pfade & Speicherung
    base_dir: Path = BASE_DIR
    chroma_dir: str = Field(default_factory=lambda: os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "chroma_db")))
    data_dir: Path = BASE_DIR / "data"
    
    # RAG Parameter
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k_candidates: int = 12   # Kandidaten für Hybrid-Search
    top_k_final: int = 4         # Nach FlashRank Re-Ranking an LLM übergeben
    rrf_k: int = 60              # Reciprocal Rank Fusion Dämpfungsfaktor
    
    # Re-Ranking Modell (FlashRank auf CPU)
    reranker_model_name: str = "ms-marco-TinyBERT-L-2-v2"

# Singleton-Instanz
config = AppConfig()
