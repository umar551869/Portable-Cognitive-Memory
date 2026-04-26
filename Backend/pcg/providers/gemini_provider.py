from __future__ import annotations

import asyncio
import importlib
from typing import Any, Sequence

from pcg.config.settings import settings
from pcg.providers.base import LLMProvider
from pcg.providers.prompts import build_entity_extraction_prompt, build_relationship_extraction_prompt
from pcg.utils.schemas import EntityExtractionResult, RelationshipExtractionResult


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        api_key = settings.secret_value(settings.gemini_api_key)
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        module = importlib.import_module("google.genai")
        self.client: Any = module.Client(api_key=api_key)
        self.chat_model = settings.gemini_chat_model
        self.embedding_model = settings.gemini_embedding_model

    async def extract_entities(self, text: str) -> EntityExtractionResult:
        prompt = build_entity_extraction_prompt(text)

        def _call() -> str:
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            return response.text

        return EntityExtractionResult.model_validate_json(await asyncio.to_thread(_call))

    async def extract_relationships(self, text: str, entities: Sequence[str]) -> RelationshipExtractionResult:
        prompt = build_relationship_extraction_prompt(text, entities)

        def _call() -> str:
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            return response.text

        return RelationshipExtractionResult.model_validate_json(await asyncio.to_thread(_call))

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        def _call() -> list[list[float]]:
            vectors: list[list[float]] = []
            for value in texts:
                response = self.client.models.embed_content(
                    model=self.embedding_model,
                    contents=value,
                )
                vectors.append(response.embeddings[0].values)
            return vectors

        return await asyncio.to_thread(_call)
