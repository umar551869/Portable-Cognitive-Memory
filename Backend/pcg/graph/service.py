from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.graph_repository import GraphRepository


class GraphService:
    """Read-only graph traversal helpers."""

    def __init__(self, session: AsyncSession):
        self.repository = GraphRepository(session)

    async def expand_neighbors(self, user_id: UUID, node_ids: list[UUID], max_hops: int = 2):
        return await self.repository.get_neighbors(user_id, node_ids, max_hops=max_hops)
