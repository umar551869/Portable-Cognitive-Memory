from __future__ import annotations

from typing import Dict, Sequence
from uuid import UUID, uuid5, NAMESPACE_URL

from pcg.config.settings import settings
from pcg.entity_resolution.normalization import normalize
from pcg.storage.embedding_repository import EmbeddingRepository
from pcg.storage.node_repository import NodeRepository
from pcg.utils.schemas import EntityCandidate, ResolvedNode


class EntityResolver:
    """Resolve extracted entities to stable graph node IDs."""

    def __init__(self, node_repository: NodeRepository, embedding_repository: EmbeddingRepository):
        self.nodes = node_repository
        self.embeddings = embedding_repository

    async def resolve_entities(
        self,
        entities: Sequence[EntityCandidate],
        *,
        user_id: UUID,
        session_id: str | None,
        project_id: str | None,
        chunk_embedding_inputs: Dict[str, list[float]],
    ) -> tuple[Dict[str, UUID], list[ResolvedNode]]:
        temp_id_map: Dict[str, UUID] = {}
        resolved_nodes: list[ResolvedNode] = []

        for entity in entities:
            canonical_name = normalize(entity.name)
            if not canonical_name:
                continue

            existing = await self.nodes.get_by_canonical_name(user_id, canonical_name)
            if existing is not None:
                final_id = existing.id
                aliases = sorted(set((existing.aliases or []) + entity.aliases + [entity.name]))
                resolved_nodes.append(
                    ResolvedNode(
                        id=final_id,
                        user_id=user_id,
                        canonical_name=canonical_name,
                        display_name=entity.name.strip(),
                        type=entity.type,
                        aliases=aliases,
                        description=entity.description,
                        metadata=entity.metadata,
                        session_id=session_id,
                        project_id=project_id,
                        weight=1,
                    )
                )
                temp_id_map[entity.temp_id] = final_id
                continue

            embedding = chunk_embedding_inputs.get(entity.temp_id)
            final_id = uuid5(NAMESPACE_URL, f"pcg-node:{user_id}:{canonical_name}")
            if embedding:
                matches = await self.embeddings.search(
                    user_id,
                    embedding,
                    owner_type="node",
                    top_k=1,
                )
                if matches and matches[0].similarity >= settings.deduplication_threshold and matches[0].embedding.node_id:
                    final_id = matches[0].embedding.node_id

            resolved_nodes.append(
                ResolvedNode(
                    id=final_id,
                    user_id=user_id,
                    canonical_name=canonical_name,
                    display_name=entity.name.strip(),
                    type=entity.type,
                    aliases=sorted(set(entity.aliases + [entity.name.strip()])),
                    description=entity.description,
                    metadata=entity.metadata,
                    session_id=session_id,
                    project_id=project_id,
                    weight=1,
                )
            )
            temp_id_map[entity.temp_id] = final_id

        return temp_id_map, resolved_nodes
