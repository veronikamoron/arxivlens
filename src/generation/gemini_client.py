"""
Google Gemini LLM Client (gemini-2.0-flash / gemini-1.5-flash).
Unterstützt Streaming-Antworten und dynamisches Key-Management im Free Tier.
"""

from typing import Optional, Generator
import google.generativeai as genai
from ..config import config
from .prompts import PromptTemplates

class GeminiLLMClient:
    """Wrapper für Google Gemini Modelle mit Streaming-Unterstützung."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key
        self.model_name = model_name or "gemini-3.6-flash"
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def set_api_key(self, api_key: str):
        """Aktualisiert den API-Key dynamisch (z.B. aus dem Streamlit UI)."""
        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def _get_model(self, model_name: str, system_instruction: Optional[str] = None) -> genai.GenerativeModel:
        """Initialisiert das Modell mit System-Prompt."""
        if not self.api_key:
            raise ValueError("Kein Google Gemini API-Key hinterlegt. Bitte trage deinen kostenlosen API-Key in der linken Seitenleiste ein.")

        instruction = system_instruction or PromptTemplates.SYSTEM_PROMPT
        return genai.GenerativeModel(
            model_name=model_name,
            system_instruction=instruction,
            generation_config={"temperature": 0.2, "top_p": 0.95}
        )

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generiert eine vollständige Antwort als String."""
        models_to_try = [self.model_name, "gemini-3.6-flash", "models/gemini-3.6-flash"]
        last_error = None
        for m_name in models_to_try:
            try:
                model = self._get_model(m_name, system_instruction)
                response = model.generate_content(prompt)
                self.model_name = m_name
                return response.text
            except Exception as e:
                last_error = e
                continue
        raise last_error

    def generate_stream(self, prompt: str, system_instruction: Optional[str] = None) -> Generator[str, None, None]:
        """Generiert eine Antwort als Stream von Token-Chunks (ideal für Streamlit UI)."""
        models_to_try = [self.model_name, "gemini-3.6-flash", "models/gemini-3.6-flash"]
        for m_name in models_to_try:
            try:
                model = self._get_model(m_name, system_instruction)
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                self.model_name = m_name
                return
            except Exception:
                continue
        # Fallback zum finalen Versuch
        model = self._get_model("gemini-3.6-flash", system_instruction)
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

