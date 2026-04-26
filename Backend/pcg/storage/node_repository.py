from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import Node
from pcg.utils.schemas import ResolvedNode


class NodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID, node_id: UUID) -> Node | None:
        return await self.session.scalar(select(Node).where(Node.user_id == user_id, Node.id == node_id))

    async def get_by_canonical_name(self, user_id: UUID, canonical_name: str) -> Node | None:
        return await self.session.scalar(
            select(Node).where(Node.user_id == user_id, Node.canonical_name == canonical_name)
        )

    async def get_by_name(self, user_id: UUID, name: str) -> Node | None:
        """Alias for get_by_canonical_name, used by structural extractor."""
        return await self.get_by_canonical_name(user_id, name)

    async def list_all(self, user_id: UUID) -> list[Node]:
        result = await self.session.scalars(select(Node).where(Node.user_id == user_id))
        return list(result.all())

    async def upsert(self, node: ResolvedNode) -> Node:
        existing = await self.get_by_canonical_name(node.user_id, node.canonical_name)
        if existing is None:
            # Also check by ID to prevent UNIQUE constraint on id
            existing = await self.get_by_id(node.user_id, node.id)
        if existing is None:
            existing = Node(
                id=node.id,
                user_id=node.user_id,
                canonical_name=node.canonical_name,
                display_name=node.display_name,
                type=node.type,
                aliases=sorted(set(node.aliases)),
                description=node.description,
                metadata_json=node.metadata,
                weight=node.weight,
                session_id=node.session_id,
                project_id=node.project_id,
            )
            self.session.add(existing)
        else:
            existing.display_name = node.display_name or existing.display_name
            existing.type = node.type or existing.type
            existing.aliases = sorted(set((existing.aliases or []) + node.aliases))
            existing.description = node.description or existing.description
            existing.metadata_json = {**(existing.metadata_json or {}), **node.metadata}
            existing.weight += max(node.weight, 1)
            existing.session_id = node.session_id or existing.session_id
            existing.project_id = node.project_id or existing.project_id
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            # On conflict, try to merge instead
            existing_by_id = await self.get_by_id(node.user_id, node.id)
            if existing_by_id:
                existing_by_id.weight += 1
                await self.session.commit()
                return existing_by_id
            raise
        await self.session.refresh(existing)
        return existing

    async def delete_all_for_user(self, user_id: UUID) -> None:
        rows = await self.session.scalars(select(Node).where(Node.user_id == user_id))
        for row in rows:
            await self.session.delete(row)
        await self.session.commit()
