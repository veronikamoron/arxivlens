"""
Google Gemini Embedding Client (text-embedding-004).
Erzeugt hochwertige semantische Vektoren für wissenschaftliche Dokumente und Suchanfragen.
"""

from typing import List, Optional
import google.generativeai as genai
from ..config import config

class GeminiEmbeddingClient:
    """Wrapper für Googles text-embedding-004 API."""

    # ==============================================================================
    # STRIKTE FREE-TIER WHITELIST (NUR 100 % KOSTENLOSE GOOGLE MODELLE)
    # Verhindert garantiert die Nutzung jeglicher kostenpflichtiger Modelle.
    # ==============================================================================
    FREE_TIER_MODELS = [
        "models/embedding-001",
        "models/text-embedding-004",
        "embedding-001",
        "text-embedding-004"
    ]

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key
        self.model_name = model_name or "models/embedding-001"
        self._resolved_model: Optional[str] = None
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def set_api_key(self, api_key: str):
        """Aktualisiert den API-Key dynamisch (z.B. bei Eingabe im Streamlit-Frontend)."""
        self.api_key = api_key
        self._resolved_model = None
        genai.configure(api_key=self.api_key)

    def _get_active_model(self) -> str:
        """
        Ermittelt dynamisch das passende Modell – STRIKT BESCHRÄNKT auf den 100% Free-Tier.
        Schließt alle potenziell kostenpflichtigen Modelle garantiert aus.
        """
        if self._resolved_model:
            return self._resolved_model

        # 1. Abfrage der vom API-Key unterstützten Modelle
        try:
            available_models = [
                m.name for m in genai.list_models()
                if "embedContent" in getattr(m, "supported_generation_methods", [])
            ]
            # 2. STRIKTES FILTERN: Nur Modelle zulassen, die in der Free-Tier Whitelist stehen!
            free_available = [
                m for m in available_models
                if any(free in m for free in ["text-embedding-004", "embedding-001"])
            ]

            # text-embedding-004 bevorzugen (falls im Free Tier aktiv), sonst embedding-001
            for m in free_available:
                if "text-embedding-004" in m:
                    self._resolved_model = m
                    return self._resolved_model

            for m in free_available:
                if "embedding-001" in m:
                    self._resolved_model = m
                    return self._resolved_model

        except Exception as e:
            print(f"[Embedding Info] Modellabfrage nicht möglich ({e}). Verwende garantierten Free-Tier Standard.")

        # 3. Absoluter Sicherheits-Standard: models/embedding-001 (dauerhaft 0,00 € Free Tier)
        self._resolved_model = "models/embedding-001"
        return self._resolved_model


    def embed_documents(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Erzeugt Vektor-Embeddings für eine Liste von Text-Chunks in Batches mit Auto-Fallback."""
        if not self.api_key:
            raise ValueError("Kein Google Gemini API Key gesetzt. Bitte in .env oder im UI eintragen.")

        model_to_use = self._get_active_model()
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                result = genai.embed_content(
                    model=model_to_use,
                    content=batch,
                    task_type="retrieval_document"
                )
                all_embeddings.extend(result["embedding"])
            except Exception as e:
                # Falls das Modell fehlschlägt (z.B. 404), sofort universelles Fallback versuchen
                if model_to_use != "models/embedding-001":
                    print(f"[Embedding Fallback] {model_to_use} nicht verfügbar ({e}). Wechsle zu models/embedding-001.")
                    self._resolved_model = "models/embedding-001"
                    result = genai.embed_content(
                        model=self._resolved_model,
                        content=batch,
                        task_type="retrieval_document"
                    )
                    all_embeddings.extend(result["embedding"])
                else:
                    raise e

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Erzeugt das Vektor-Embedding für eine Suchanfrage des Nutzers."""
        if not self.api_key:
            raise ValueError("Kein Google Gemini API Key gesetzt. Bitte in .env oder im UI eintragen.")

        model_to_use = self._get_active_model()
        try:
            result = genai.embed_content(
                model=model_to_use,
                content=query,
                task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            if model_to_use != "models/embedding-001":
                self._resolved_model = "models/embedding-001"
                result = genai.embed_content(
                    model=self._resolved_model,
                    content=query,
                    task_type="retrieval_query"
                )
                return result["embedding"]
            raise e

