"""
Generation-Module: Google Gemini API Client und wissenschaftliche Prompt-Templates.
"""

from .gemini_client import GeminiLLMClient
from .prompts import PromptTemplates

__all__ = ["GeminiLLMClient", "PromptTemplates"]
