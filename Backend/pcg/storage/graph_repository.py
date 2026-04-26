from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Edge, Node, RawLog


class GraphRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_neighbors(self, user_id: UUID, node_ids: list[UUID], max_hops: int = 2) -> tuple[dict[UUID, Node], list[Edge]]:
        seen = set(node_ids)
        frontier = set(node_ids)
        nodes: dict[UUID, Node] = {}
        edges: dict[UUID, Edge] = {}

        for _ in range(max_hops):
            if not frontier:
                break
            result = await self.session.scalars(
                select(Edge).where(Edge.user_id == user_id, or_(Edge.source_id.in_(frontier), Edge.target_id.in_(frontier)))
            )
            next_frontier: set[UUID] = set()
            for edge in result:
                edges[edge.id] = edge
                next_frontier.add(edge.source_id)
                next_frontier.add(edge.target_id)
            frontier = next_frontier - seen
            seen.update(next_frontier)

        if seen:
            node_rows = await self.session.scalars(select(Node).where(Node.user_id == user_id, Node.id.in_(seen)))
            for node in node_rows:
                nodes[node.id] = node

        return nodes, list(edges.values())

    async def get_raw_logs_by_ids(self, user_id: UUID, raw_log_ids: list[UUID]) -> dict[UUID, RawLog]:
        if not raw_log_ids:
            return {}
        rows = await self.session.scalars(select(RawLog).where(RawLog.user_id == user_id, RawLog.id.in_(raw_log_ids)))
        return {row.id: row for row in rows}
