from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Embedding
from pcg.utils.schemas import EmbeddingRecord


@dataclass(slots=True)
class EmbeddingMatch:
    embedding: Embedding
    similarity: float


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class EmbeddingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, embedding: EmbeddingRecord) -> Embedding:
        existing = await self.session.get(Embedding, embedding.id)
        if existing:
            existing.node_id = embedding.node_id
            existing.chunk_id = embedding.chunk_id
            existing.raw_log_id = embedding.raw_log_id
            existing.content = embedding.content
            existing.embedding = embedding.embedding
            existing.metadata_json = embedding.metadata
            existing.session_id = embedding.session_id
            existing.project_id = embedding.project_id
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        
        record = Embedding(
            id=embedding.id,
            user_id=embedding.user_id,
            owner_type=embedding.owner_type,
            node_id=embedding.node_id,
            chunk_id=embedding.chunk_id,
            raw_log_id=embedding.raw_log_id,
            content=embedding.content,
            embedding=embedding.embedding,
            embedding_model=embedding.embedding_model,
            embedding_version=embedding.embedding_version,
            metadata_json=embedding.metadata,
            session_id=embedding.session_id,
            project_id=embedding.project_id,
        )
        self.session.add(record)
        try:
            await self.session.commit()
            await self.session.refresh(record)
            return record
        except Exception:
            await self.session.rollback()
            # Fallback to merge if commit failed (e.g. race condition)
            return await self.session.merge(record)

    async def add(self, embedding: EmbeddingRecord) -> Embedding:
        return await self.upsert(embedding)

    async def list_for_user(self, user_id: UUID, owner_type: str | None = None) -> list[Embedding]:
        stmt = select(Embedding).where(Embedding.user_id == user_id)
        if owner_type:
            stmt = stmt.where(Embedding.owner_type == owner_type)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def delete_owner_embeddings(self, user_id: UUID, owner_type: str) -> None:
        rows = await self.session.scalars(
            select(Embedding).where(Embedding.user_id == user_id, Embedding.owner_type == owner_type)
        )
        for row in rows:
            await self.session.delete(row)
        await self.session.commit()

    async def search(
        self,
        user_id: UUID,
        query_embedding: Sequence[float],
        *,
        owner_type: str,
        model: str | None = None,
        version: str | None = None,
        top_k: int = 5,
    ) -> list[EmbeddingMatch]:
        stmt = select(Embedding).where(Embedding.user_id == user_id, Embedding.owner_type == owner_type)
        if model is not None:
            stmt = stmt.where(Embedding.embedding_model == model)
        if version is not None:
            stmt = stmt.where(Embedding.embedding_version == version)
        rows = await self.session.scalars(stmt)
        matches = [
            EmbeddingMatch(embedding=row, similarity=cosine_similarity(query_embedding, row.embedding or []))
            for row in rows
        ]
        matches.sort(key=lambda item: item.similarity, reverse=True)
        return matches[:top_k]
