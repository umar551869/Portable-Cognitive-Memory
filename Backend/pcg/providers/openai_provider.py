from __future__ import annotations

import openai

from pcg.config.settings import settings
from pcg.providers.base import LLMProvider
from pcg.providers.prompts import build_entity_extraction_prompt, build_relationship_extraction_prompt
from pcg.utils.schemas import EntityExtractionResult, RelationshipExtractionResult


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        api_key = settings.secret_value(settings.openai_api_key)
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.chat_model = settings.openai_chat_model
        self.embedding_model = settings.openai_embedding_model

    async def extract_entities(self, text: str) -> EntityExtractionResult:
        response = await self.client.responses.create(
            model=self.chat_model,
            input=build_entity_extraction_prompt(text),
            text={"format": {"type": "json_object"}},
        )
        return EntityExtractionResult.model_validate_json(response.output_text)

    async def extract_relationships(self, text: str, entities: list[str]) -> RelationshipExtractionResult:
        response = await self.client.responses.create(
            model=self.chat_model,
            input=build_relationship_extraction_prompt(text, entities),
            text={"format": {"type": "json_object"}},
        )
        return RelationshipExtractionResult.model_validate_json(response.output_text)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(input=texts, model=self.embedding_model)
        return [item.embedding for item in response.data]
