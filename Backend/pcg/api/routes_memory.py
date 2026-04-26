from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.api.deps import get_session
from pcg.api.limiter import limiter
from pcg.auth.dependencies import get_current_user
from pcg.processing.pipeline import ProcessingPipeline, build_raw_log
from pcg.retrieval.search import RetrievalService
from pcg.storage.db import get_session_factory
from pcg.storage.edge_repository import EdgeRepository
from pcg.storage.node_repository import NodeRepository
from pcg.storage.stats_repository import StatsRepository
from pcg.utils.schemas import (
    GraphResponse,
    IngestRequest,
    IngestResponse,
    RebuildResponse,
    RecallResult,
    ReindexRequest,
    RetrievalEdge,
    RetrievalNode,
    IngestDirectoryRequest,
)
from pcg.ingestion.system_discovery import DiscoveryService
from pcg.ingestion.file_monitor import start_file_monitor


router = APIRouter(tags=["memory"])


async def _run_ingest_task(user_id, payload: IngestRequest) -> None:
    async with get_session_factory()() as session:
        await ProcessingPipeline(session).process_ingest_request(user_id, payload)


async def _run_reindex_task(user_id, provider: str, model: str, version: str) -> None:
    async with get_session_factory()() as session:
        await ProcessingPipeline(session).reindex_embeddings(user_id, provider, model, version)


async def _run_rebuild_task(user_id) -> None:
    async with get_session_factory()() as session:
        await ProcessingPipeline(session).rebuild_graph(user_id)


async def _run_ingest_directory_task(user_id, path: str, project_id: str) -> None:
    import os
    from pathlib import Path
    
    INGESTABLE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".sql", ".sh", ".md", ".txt", ".json", ".yml", ".yaml", ".html", ".css"
    }
    SKIP_DIRS = {"node_modules", ".git", ".next", "__pycache__", ".venv", "venv"}

    async with get_session_factory()() as session:
        pipeline = ProcessingPipeline(session)
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix.lower() in INGESTABLE_EXTENSIONS:
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        if len(content.strip()) > 50:
                            req = IngestRequest(source_path=str(fpath), content=content, project_id=project_id)
                            await pipeline.process_ingest_request(user_id, req)
                    except Exception:
                        continue


@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("100/hour")
async def ingest(
    request: Request,
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> IngestResponse:
    del session
    raw_log = build_raw_log(current_user.id, payload)
    background_tasks.add_task(_run_ingest_task, current_user.id, payload)
    return IngestResponse(raw_log_id=raw_log.id, status="queued")


@router.post("/ingest-directory", response_model=RebuildResponse)
@limiter.limit("5/day")
async def ingest_directory(
    request: Request,
    payload: IngestDirectoryRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
) -> RebuildResponse:
    background_tasks.add_task(_run_ingest_directory_task, current_user.id, payload.path, payload.project_id)
    return RebuildResponse(status="queued")


@router.get("/recall", response_model=RecallResult)
@limiter.limit("300/hour")
async def recall(
    request: Request,
    q: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> RecallResult:
    return await RetrievalService(session).recall(current_user.id, q)


@router.post("/reindex", response_model=RebuildResponse)
@limiter.limit("2/hour")
async def reindex(
    request: Request,
    payload: ReindexRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> RebuildResponse:
    del session
    background_tasks.add_task(_run_reindex_task, current_user.id, payload.provider, payload.model, payload.version)
    return RebuildResponse(status="queued")


@router.post("/rebuild", response_model=RebuildResponse)
@limiter.limit("2/hour")
async def rebuild(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> RebuildResponse:
    del session
    background_tasks.add_task(_run_rebuild_task, current_user.id)
    return RebuildResponse(status="queued")


@router.get("/discovery/scan")
@limiter.limit("5/minute")
async def scan_system(request: Request, current_user=Depends(get_current_user)):
    paths = DiscoveryService.get_starter_paths()
    return {"paths": [str(p) for p in paths]}


@router.post("/discovery/watch")
@limiter.limit("5/minute")
async def watch_system(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    paths = DiscoveryService.get_starter_paths()
    exts = [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".json", ".sql"]
    
    # Start monitor for each path as background tasks
    # In a real app, we would manage these task objects and prevent duplicates
    for path in paths:
        if path.exists():
            background_tasks.add_task(start_file_monitor, current_user.id, str(path), exts)
            
    return {"status": "monitoring_engaged", "path_count": len(paths)}


@router.get("/stats")
@limiter.limit("60/minute")
async def stats(request: Request, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    return await StatsRepository(session).get_graph_stats(current_user.id)


@router.get("/graph", response_model=GraphResponse)
@limiter.limit("10/minute")
async def graph(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> GraphResponse:
    nodes = await NodeRepository(session).list_all(current_user.id)
    edges = await EdgeRepository(session).list_all(current_user.id)
    return GraphResponse(
        nodes=[
            RetrievalNode(
                id=node.id,
                canonical_name=node.canonical_name,
                display_name=node.display_name,
                type=node.type,
                aliases=node.aliases or [],
                description=node.description,
                metadata=node.metadata_json or {},
                weight=node.weight,
                score=0.0,
            )
            for node in nodes
        ],
        edges=[
            RetrievalEdge(
                source_id=edge.source_id,
                target_id=edge.target_id,
                relation=edge.relation,
                weight=edge.weight,
                evidence=edge.evidence,
            )
            for edge in edges
        ],
    )
