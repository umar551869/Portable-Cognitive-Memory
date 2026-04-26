from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pcg.config.settings import settings
from pcg.providers.factory import get_provider
from pcg.storage.embedding_repository import EmbeddingRepository
from pcg.storage.graph_repository import GraphRepository
from pcg.storage.node_repository import NodeRepository
from pcg.utils.schemas import RecallResult, RetrievalEdge, RetrievalNode, RetrievalRawLog


class RetrievalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embeddings = EmbeddingRepository(session)
        self.graph = GraphRepository(session)
        self.nodes = NodeRepository(session)

    async def recall(self, user_id: UUID, query: str, top_k: int = settings.retrieval_top_k) -> RecallResult:
        provider = get_provider()
        query_embedding = (await provider.embed([query]))[0]
        node_matches = await self.embeddings.search(
            user_id,
            query_embedding,
            owner_type="node",
            model=provider.embedding_model,
            version=settings.embedding_version,
            top_k=top_k,
        )
        seed_ids = [match.embedding.node_id for match in node_matches if match.embedding.node_id is not None]
        graph_nodes, graph_edges = await self.graph.get_neighbors(user_id, [node_id for node_id in seed_ids if node_id], max_hops=settings.graph_hops)

        connectivity: dict[UUID, int] = defaultdict(int)
        for edge in graph_edges:
            connectivity[edge.source_id] += 1
            connectivity[edge.target_id] += 1

        similarity_lookup = {match.embedding.node_id: match.similarity for match in node_matches}
        max_weight = max((node.weight for node in graph_nodes.values()), default=1)
        max_connectivity = max(connectivity.values(), default=1)
        ranked_nodes: list[RetrievalNode] = []
        for node in graph_nodes.values():
            similarity = similarity_lookup.get(node.id, 0.0)
            score = (similarity * 0.6) + ((node.weight / max_weight) * 0.2) + ((connectivity[node.id] / max_connectivity) * 0.2)
            ranked_nodes.append(
                RetrievalNode(
                    id=node.id,
                    canonical_name=node.canonical_name,
                    display_name=node.display_name,
                    type=node.type,
                    aliases=node.aliases or [],
                    description=node.description,
                    metadata=node.metadata_json or {},
                    weight=node.weight,
                    score=score,
                )
            )
        ranked_nodes.sort(key=lambda item: item.score, reverse=True)

        chunk_matches = await self.embeddings.search(
            user_id,
            query_embedding,
            owner_type="chunk",
            model=provider.embedding_model,
            version=settings.embedding_version,
            top_k=5,
        )
        raw_logs = await self.graph.get_raw_logs_by_ids(
            user_id,
            [match.embedding.raw_log_id for match in chunk_matches if match.embedding.raw_log_id is not None],
        )

        return RecallResult(
            query=query,
            nodes=ranked_nodes,
            edges=[
                RetrievalEdge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relation=edge.relation,
                    weight=edge.weight,
                    evidence=edge.evidence,
                )
                for edge in graph_edges
            ],
            raw_logs=[
                RetrievalRawLog(
                    id=raw_log.id,
                    source_path=raw_log.source_path,
                    excerpt=match.embedding.content[:400],
                    score=match.similarity,
                )
                for match in chunk_matches
                if match.embedding.raw_log_id in raw_logs
                for raw_log in [raw_logs[match.embedding.raw_log_id]]
            ],
        )
