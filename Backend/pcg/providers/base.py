from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from pcg.utils.schemas import EntityExtractionResult, RelationshipExtractionResult


class LLMProvider(ABC):
    """Unified provider interface for extraction and embedding."""

    name: str
    embedding_model: str

    @abstractmethod
    async def extract_entities(self, text: str) -> EntityExtractionResult:
        raise NotImplementedError

    @abstractmethod
    async def extract_relationships(
        self,
        text: str,
        entities: Sequence[str],
    ) -> RelationshipExtractionResult:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError
