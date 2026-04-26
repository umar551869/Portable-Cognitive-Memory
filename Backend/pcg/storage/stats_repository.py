from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Chunk, Edge, Embedding, Node, RawLog
from pcg.utils.schemas import GraphStats


class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_graph_stats(self, user_id: UUID) -> GraphStats:
        node_count = await self.session.scalar(select(func.count()).select_from(Node).where(Node.user_id == user_id)) or 0
        edge_count = await self.session.scalar(select(func.count()).select_from(Edge).where(Edge.user_id == user_id)) or 0
        embedding_count = await self.session.scalar(select(func.count()).select_from(Embedding).where(Embedding.user_id == user_id)) or 0
        raw_log_count = await self.session.scalar(select(func.count()).select_from(RawLog).where(RawLog.user_id == user_id)) or 0
        chunk_count = await self.session.scalar(select(func.count()).select_from(Chunk).where(Chunk.user_id == user_id)) or 0
        return GraphStats(
            node_count=node_count,
            edge_count=edge_count,
            embedding_count=embedding_count,
            raw_log_count=raw_log_count,
            chunk_count=chunk_count,
        )
