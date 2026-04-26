from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid5, NAMESPACE_URL

from sqlalchemy.ext.asyncio import AsyncSession

from pcg.config.settings import settings
from pcg.entity_resolution.normalization import normalize
from pcg.entity_resolution.resolver import EntityResolver
from pcg.processing.chunking import build_chunks
from pcg.providers.base import LLMProvider
from pcg.processing.structural_extractor import StructuralExtractor
from pcg.providers.factory import get_provider
from pcg.providers.prompts import DISALLOWED_RELATIONS
from pcg.storage.chunk_repository import ChunkRepository
from pcg.storage.edge_repository import EdgeRepository
from pcg.storage.embedding_repository import EmbeddingRepository
from pcg.storage.node_repository import NodeRepository
from pcg.storage.raw_log_repository import RawLogRepository
from pcg.utils.logging import get_logger
from pcg.utils.schemas import EdgeRecord, EmbeddingRecord, IngestRequest, RawLog


logger = get_logger("pipeline")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def validate_safe_path(path: str) -> bool:
    """Ensure path is within the allowed workspace or is a virtual URI."""
    if not path:
        return True
    if path.startswith(("text://", "history://", "starters://")):
        return True
    # In a real industrial app, we would check against a list of allowed root directories.
    # For this local FYP, we'll ensure it doesn't try to go up into system dirs.
    abs_path = os.path.abspath(path)
    # Block common sensitive system paths
    forbidden = ["C:\\Windows", "/etc/", "/root", "C:\\Users\\Default"]
    for f in forbidden:
        if abs_path.lower().startswith(f.lower()):
            return False
    return True

def build_raw_log(user_id: UUID, payload: IngestRequest) -> RawLog:
    if not validate_safe_path(payload.source_path):
        raise ValueError(f"Insecure source path detected: {payload.source_path}")
    content_hash = _sha256(payload.content)
    raw_log_id = uuid5(NAMESPACE_URL, f"pcg-raw-log:{user_id}:{payload.source_path}:{content_hash}")
    return RawLog(
        id=raw_log_id,
        user_id=user_id,
        source_path=payload.source_path,
        content=payload.content,
        content_hash=content_hash,
        session_id=payload.session_id,
        project_id=payload.project_id,
        file_modified_at=datetime.now(timezone.utc),
    )


@dataclass(slots=True)
class PipelineResult:
    raw_log_id: UUID
    chunk_count: int
    node_count: int
    edge_count: int


class ProcessingPipeline:
    """Graph-building pipeline scoped to a single authenticated user."""

    def __init__(self, session: AsyncSession, provider: LLMProvider | None = None):
        self.session = session
        self.provider = provider or get_provider()
        self.node_repository = NodeRepository(session)
        self.edge_repository = EdgeRepository(session)
        self.embedding_repository = EmbeddingRepository(session)
        self.raw_log_repository = RawLogRepository(session)
        self.chunk_repository = ChunkRepository(session)
        self.resolver = EntityResolver(self.node_repository, self.embedding_repository)
        self.structural_extractor = StructuralExtractor()

    async def process_ingest_request(self, user_id: UUID, payload: IngestRequest) -> PipelineResult:
        raw_log = build_raw_log(user_id, payload)
        stored_raw_log = await self.raw_log_repository.upsert(raw_log)
        return await self.process_raw_log(stored_raw_log.user_id, raw_log)

    async def process_raw_log(self, user_id: UUID, raw_log: RawLog) -> PipelineResult:
        logger.info("ingestion_start user_id=%s raw_log_id=%s path=%s", user_id, raw_log.id, raw_log.source_path)
        stored_raw_log = await self.raw_log_repository.upsert(raw_log)
        node_count = 0
        edge_count = 0
        chunk_count = 0
        # --- STAGE 0: Structural Extraction (AST) ---
        structural_nodes = []
        structural_edges = []
        if raw_log.source_path and os.path.exists(raw_log.source_path):
            struct_result = self.structural_extractor.extract(raw_log.source_path)
            if struct_result["nodes"]:
                logger.info("structural_extraction_complete nodes=%s edges=%s", len(struct_result["nodes"]), len(struct_result["edges"]))
                entities = self.structural_extractor.convert_to_pcg_entities(struct_result)
                
                # Resolve and upsert structural nodes
                temp_id_map, resolved_nodes = await self.resolver.resolve_entities(
                    entities,
                    user_id=user_id,
                    session_id=raw_log.session_id,
                    project_id=raw_log.project_id,
                    chunk_embedding_inputs={} # No embeddings for AST nodes yet
                )
                for node in resolved_nodes:
                    await self.node_repository.upsert(node)
                    node_count += 1
                
                # Convert edges
                structural_edges = self.structural_extractor.convert_to_pcg_relationships(struct_result)
                for rel in structural_edges:
                    # Logic to upsert edges based on names (similar to relationship stage)
                    # For now, we'll store them and let the relationship stage handle them if possible
                    # or implement a simple edge upsert here.
                    src_node = await self.node_repository.get_by_name(user_id, rel["source_name"])
                    tgt_node = await self.node_repository.get_by_name(user_id, rel["target_name"])
                    if src_node and tgt_node:
                        await self.edge_repository.upsert(
                            build_edge(
                                user_id=user_id,
                                source_id=src_node.id,
                                target_id=tgt_node.id,
                                relation=rel["relation"],
                                weight=rel["weight"],
                                evidence=rel["evidence"],
                                session_id=raw_log.session_id,
                                project_id=raw_log.project_id,
                            )
                        )
                        edge_count += 1

        # --- STAGE 1: Chunking ---
        chunks = build_chunks(
            raw_log_id=stored_raw_log.id,
            user_id=user_id,
            source_path=stored_raw_log.source_path,
            content=stored_raw_log.content,
            session_id=stored_raw_log.session_id,
            project_id=stored_raw_log.project_id,
        )
        stored_chunks = await self.chunk_repository.replace_for_raw_log(user_id, stored_raw_log.id, chunks)

        node_count = 0
        edge_count = 0

        for chunk in stored_chunks:
            try:
                chunk_embedding = (await self.provider.embed([chunk.content]))[0]
                await self.embedding_repository.add(
                    EmbeddingRecord(
                        id=uuid5(
                            NAMESPACE_URL,
                            f"{user_id}:chunk:{chunk.id}:{self.provider.embedding_model}:{settings.embedding_version}",
                        ),
                        owner_type="chunk",
                        user_id=user_id,
                        chunk_id=chunk.id,
                        raw_log_id=stored_raw_log.id,
                        content=chunk.content,
                        embedding=chunk_embedding,
                        embedding_model=self.provider.embedding_model,
                        embedding_version=settings.embedding_version,
                        session_id=stored_raw_log.session_id,
                        project_id=stored_raw_log.project_id,
                        metadata={"source_path": stored_raw_log.source_path},
                    )
                )
                entity_result = await self._run_with_fallback("extract_entities", chunk.content)
            except Exception as exc:  # noqa: BLE001
                logger.exception("entity_stage_failed user_id=%s chunk_id=%s error=%s", user_id, chunk.id, exc)
                continue

            embedding_inputs = [
                self._build_embedding_input(
                    name=entity.name,
                    aliases=entity.aliases,
                    node_type=entity.type,
                    description=entity.description,
                    metadata=entity.metadata,
                )
                for entity in entity_result.entities
            ]
            entity_vectors = await self._embed_with_fallback(embedding_inputs) if embedding_inputs else []
            vector_map = {entity.temp_id: vector for entity, vector in zip(entity_result.entities, entity_vectors)}

            filtered_entities = self._filter_entities(entity_result.entities)
            temp_id_map, resolved_nodes = await self.resolver.resolve_entities(
                filtered_entities,
                user_id=user_id,
                session_id=stored_raw_log.session_id,
                project_id=stored_raw_log.project_id,
                chunk_embedding_inputs=vector_map,
            )

            for entity, resolved_node in zip(filtered_entities, resolved_nodes):
                node = await self.node_repository.upsert(resolved_node)
                node_count += 1
                await self.embedding_repository.add(
                    EmbeddingRecord(
                        id=uuid5(
                            NAMESPACE_URL,
                            f"{user_id}:node:{node.id}:{self.provider.embedding_model}:{settings.embedding_version}:{entity.temp_id}",
                        ),
                        owner_type="node",
                        user_id=user_id,
                        node_id=node.id,
                        raw_log_id=stored_raw_log.id,
                        content=self._build_embedding_input(
                            name=resolved_node.display_name,
                            aliases=resolved_node.aliases,
                            node_type=resolved_node.type,
                            description=resolved_node.description,
                            metadata=resolved_node.metadata,
                        ),
                        embedding=vector_map.get(entity.temp_id, chunk_embedding),
                        embedding_model=self.provider.embedding_model,
                        embedding_version=settings.embedding_version,
                        session_id=stored_raw_log.session_id,
                        project_id=stored_raw_log.project_id,
                        metadata={"source_path": stored_raw_log.source_path},
                    )
                )
                temp_id_map[entity.temp_id] = node.id

            try:
                relationship_result = await self._run_with_fallback(
                    "extract_relationships",
                    chunk.content,
                    [entity.name for entity in filtered_entities],
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("relationship_stage_failed user_id=%s chunk_id=%s error=%s", user_id, chunk.id, exc)
                continue

            name_to_temp = {normalize(entity.name): entity.temp_id for entity in filtered_entities}
            for relationship in self._filter_relationships(relationship_result.relationships):
                source_temp = name_to_temp.get(normalize(relationship.source_name))
                target_temp = name_to_temp.get(normalize(relationship.target_name))
                if source_temp is None or target_temp is None:
                    continue
                source_id = temp_id_map.get(source_temp)
                target_id = temp_id_map.get(target_temp)
                if source_id is None or target_id is None:
                    continue
                edge = await self.edge_repository.upsert(
                    EdgeRecord(
                        source_id=source_id,
                        target_id=target_id,
                        relation=relationship.relation,
                        user_id=user_id,
                        weight=int(max(relationship.weight, 1)),
                        session_id=stored_raw_log.session_id,
                        project_id=stored_raw_log.project_id,
                        evidence=relationship.evidence,
                    )
                )
                if edge is not None:
                    edge_count += 1

        await self.raw_log_repository.mark_processed(user_id, stored_raw_log.id)
        return PipelineResult(raw_log_id=stored_raw_log.id, chunk_count=len(stored_chunks), node_count=node_count, edge_count=edge_count)

    async def reindex_embeddings(self, user_id: UUID, provider_name: str, model: str, version: str) -> None:
        provider = get_provider(provider_name)
        provider.embedding_model = model
        await self.embedding_repository.delete_owner_embeddings(user_id, "node")
        await self.embedding_repository.delete_owner_embeddings(user_id, "chunk")

        nodes = await self.node_repository.list_all(user_id)
        for node in nodes:
            vector = (
                await provider.embed(
                    [
                        self._build_embedding_input(
                            name=node.display_name,
                            aliases=node.aliases or [],
                            node_type=node.type,
                            description=node.description,
                            metadata=node.metadata_json or {},
                        )
                    ]
                )
            )[0]
            await self.embedding_repository.add(
                EmbeddingRecord(
                    id=uuid5(NAMESPACE_URL, f"{user_id}:node:{node.id}:{model}:{version}"),
                    owner_type="node",
                    user_id=user_id,
                    node_id=node.id,
                    content=node.display_name,
                    embedding=vector,
                    embedding_model=model,
                    embedding_version=version,
                    session_id=node.session_id,
                    project_id=node.project_id,
                )
            )

        chunks = await self.chunk_repository.list_for_user(user_id)
        for chunk in chunks:
            vector = (await provider.embed([chunk.content]))[0]
            await self.embedding_repository.add(
                EmbeddingRecord(
                    id=uuid5(NAMESPACE_URL, f"{user_id}:chunk:{chunk.id}:{model}:{version}"),
                    owner_type="chunk",
                    user_id=user_id,
                    chunk_id=chunk.id,
                    raw_log_id=chunk.raw_log_id,
                    content=chunk.content,
                    embedding=vector,
                    embedding_model=model,
                    embedding_version=version,
                    session_id=chunk.session_id,
                    project_id=chunk.project_id,
                )
            )

    async def rebuild_graph(self, user_id: UUID) -> None:
        raw_logs = await self.raw_log_repository.list_all(user_id)
        await self.edge_repository.delete_all_for_user(user_id)
        await self.embedding_repository.delete_owner_embeddings(user_id, "node")
        await self.embedding_repository.delete_owner_embeddings(user_id, "chunk")
        await self.node_repository.delete_all_for_user(user_id)
        for raw_log in raw_logs:
            payload = RawLog(
                id=raw_log.id,
                user_id=raw_log.user_id,
                source_path=raw_log.source_path,
                content=raw_log.content,
                content_hash=raw_log.content_hash,
                session_id=raw_log.session_id,
                project_id=raw_log.project_id,
                file_modified_at=raw_log.file_modified_at,
            )
            await self.process_raw_log(user_id, payload)

    async def _run_with_fallback(self, method_name: str, *args):
        last_error: Exception | None = None
        
        # Build provider sequence from settings
        provider_names = [settings.llm_provider]
        if settings.fallback_llm_provider:
            # Support comma-separated fallbacks: "openai,local"
            fallbacks = [p.strip() for p in settings.fallback_llm_provider.split(",") if p.strip()]
            for f in fallbacks:
                if f not in provider_names:
                    provider_names.append(f)
        
        providers = [get_provider(name) for name in provider_names]
        
        for provider in providers:
            for _ in range(settings.llm_max_retries):
                try:
                    return await getattr(provider, method_name)(*args)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    logger.warning("provider_call_failed provider=%s method=%s error=%s", provider.name, method_name, exc)
                    
                    # If it's a quota error, don't bother retrying this provider
                    error_str = str(exc).lower()
                    if "429" in error_str or "quota" in error_str:
                        break
                        
        if last_error:
            raise last_error
        raise RuntimeError("Provider execution failed.")

    async def _embed_with_fallback(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        
        provider_names = [settings.llm_provider]
        if settings.fallback_llm_provider:
            fallbacks = [p.strip() for p in settings.fallback_llm_provider.split(",") if p.strip()]
            for f in fallbacks:
                if f not in provider_names:
                    provider_names.append(f)
                    
        providers = [get_provider(name) for name in provider_names]
        
        for provider in providers:
            for _ in range(settings.llm_max_retries):
                try:
                    return await provider.embed(texts)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    logger.warning("embed_failed provider=%s error=%s", provider.name, exc)
                    
                    error_str = str(exc).lower()
                    if "429" in error_str or "quota" in error_str:
                        break
                        
        if last_error:
            raise last_error
        raise RuntimeError("Embedding failed.")

    @staticmethod
    def _filter_entities(entities):
        banned_terms = {
            "openai",
            "gemini",
            "supabase",
            "fastapi",
            "postgresql",
            "postgres",
            "sqlite",
            "ollama",
            "llama",
        }
        filtered = []
        for entity in entities:
            name = normalize(entity.name)
            if not name or name in banned_terms:
                continue
            filtered.append(entity)
        return filtered

    @staticmethod
    def _filter_relationships(relationships):
        filtered = []
        for relationship in relationships:
            relation = normalize(relationship.relation).replace(" ", "_")
            source_name = normalize(relationship.source_name)
            target_name = normalize(relationship.target_name)
            if not source_name or not target_name or source_name == target_name:
                continue
            if relation in DISALLOWED_RELATIONS:
                continue
            filtered.append(relationship)
        return filtered

    @staticmethod
    def _build_embedding_input(
        *,
        name: str,
        aliases: list[str],
        node_type: str,
        description: str | None,
        metadata: dict[str, object],
    ) -> str:
        return (
            f"Name: {name}\n"
            f"Aliases: {', '.join(sorted(set(aliases)))}\n"
            f"Type: {node_type}\n"
            f"Context: {description or ''}\n"
            f"Metadata: {metadata}"
        )
