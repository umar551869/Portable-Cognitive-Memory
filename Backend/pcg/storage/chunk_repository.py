from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Chunk
from pcg.utils.schemas import ContentChunk


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_for_raw_log(self, user_id: UUID, raw_log_id: UUID, chunks: list[ContentChunk]) -> list[Chunk]:
        rows = await self.session.scalars(select(Chunk).where(Chunk.user_id == user_id, Chunk.raw_log_id == raw_log_id))
        for row in rows:
            await self.session.delete(row)
        await self.session.flush()

        created: list[Chunk] = []
        for chunk in chunks:
            record = Chunk(
                id=chunk.id,
                user_id=chunk.user_id,
                raw_log_id=chunk.raw_log_id,
                ordinal=chunk.ordinal,
                content=chunk.content,
                content_hash=chunk.content_hash,
                metadata_json=chunk.metadata,
                session_id=chunk.session_id,
                project_id=chunk.project_id,
            )
            self.session.add(record)
            created.append(record)
        await self.session.commit()
        for row in created:
            await self.session.refresh(row)
        return created

    async def list_for_user(self, user_id: UUID) -> list[Chunk]:
        result = await self.session.scalars(select(Chunk).where(Chunk.user_id == user_id))
        return list(result.all())
