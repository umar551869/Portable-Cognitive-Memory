from __future__ import annotations

from uuid import UUID, uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Edge
from pcg.utils.schemas import EdgeRecord


class EdgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, user_id: UUID) -> list[Edge]:
        result = await self.session.scalars(select(Edge).where(Edge.user_id == user_id))
        return list(result.all())

    async def upsert(self, edge: EdgeRecord) -> Edge | None:
        existing = await self.session.scalar(
            select(Edge).where(
                Edge.user_id == edge.user_id,
                Edge.source_id == edge.source_id,
                Edge.target_id == edge.target_id,
                Edge.relation == edge.relation,
            )
        )
        if existing is None:
            existing = Edge(
                id=uuid5(NAMESPACE_URL, f"{edge.user_id}:{edge.source_id}:{edge.target_id}:{edge.relation}"),
                user_id=edge.user_id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                relation=edge.relation,
                weight=edge.weight,
                session_id=edge.session_id,
                project_id=edge.project_id,
                evidence=edge.evidence,
            )
            self.session.add(existing)
        else:
            existing.weight += max(edge.weight, 1)
            existing.evidence = edge.evidence or existing.evidence
        await self.session.commit()
        await self.session.refresh(existing)
        return existing

    async def delete_all_for_user(self, user_id: UUID) -> None:
        rows = await self.session.scalars(select(Edge).where(Edge.user_id == user_id))
        for row in rows:
            await self.session.delete(row)
        await self.session.commit()
