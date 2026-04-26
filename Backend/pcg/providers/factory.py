from __future__ import annotations

from pcg.config.settings import settings
from pcg.providers.base import LLMProvider
from pcg.providers.gemini_provider import GeminiProvider
from pcg.providers.local_provider import LocalProvider
from pcg.providers.openai_provider import OpenAIProvider


def get_provider(name: str | None = None) -> LLMProvider:
    selected = name or settings.llm_provider
    if selected == "openai":
        return OpenAIProvider()
    if selected == "gemini":
        return GeminiProvider()
    return LocalProvider()
