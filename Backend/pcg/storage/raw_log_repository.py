from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import RawLog
from pcg.utils.schemas import RawLog as RawLogSchema


class RawLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, raw_log: RawLogSchema) -> RawLog:
        existing = await self.session.scalar(
            select(RawLog).where(RawLog.user_id == raw_log.user_id, RawLog.content_hash == raw_log.content_hash)
        )
        if existing is None:
            existing = RawLog(
                id=raw_log.id,
                user_id=raw_log.user_id,
                source_path=raw_log.source_path,
                content=raw_log.content,
                content_hash=raw_log.content_hash,
                session_id=raw_log.session_id,
                project_id=raw_log.project_id,
                file_modified_at=raw_log.file_modified_at,
            )
            self.session.add(existing)
        else:
            existing.source_path = raw_log.source_path
            existing.content = raw_log.content
            existing.session_id = raw_log.session_id
            existing.project_id = raw_log.project_id
            existing.file_modified_at = raw_log.file_modified_at
        await self.session.commit()
        await self.session.refresh(existing)
        return existing

    async def list_all(self, user_id: UUID) -> list[RawLog]:
        result = await self.session.scalars(select(RawLog).where(RawLog.user_id == user_id))
        return list(result.all())

    async def mark_processed(self, user_id: UUID, raw_log_id: UUID) -> None:
        raw_log = await self.session.scalar(select(RawLog).where(RawLog.user_id == user_id, RawLog.id == raw_log_id))
        if raw_log is None:
            return
        raw_log.processed_at = datetime.now(timezone.utc)
        await self.session.commit()
