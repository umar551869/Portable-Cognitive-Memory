from __future__ import annotations

import asyncio

import typer
import uvicorn

from pcg.api.app import app as api_app
from pcg.processing.pipeline import ProcessingPipeline
from pcg.retrieval.search import RetrievalService
from pcg.storage.db import get_db, get_engine
from pcg.storage.models import Base
from pcg.storage.stats_repository import StatsRepository
from pcg.utils.logging import configure_logging
from pcg.utils.schemas import IngestRequest


configure_logging()

app = typer.Typer(name="pcg", help="Portable Cognitive Graph CLI.")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    uvicorn.run(api_app, host=host, port=port)


@app.command()
def initdb() -> None:
    async def _init() -> None:
        async with get_engine().begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    typer.echo("Database initialized.")


@app.command()
def stats(user_id: str) -> None:
    async def _stats() -> None:
        from uuid import UUID

        async for session in get_db():
            result = await StatsRepository(session).get_graph_stats(UUID(user_id))
            typer.echo(result.model_dump_json(indent=2))

    asyncio.run(_stats())


@app.command()
def ingest(user_id: str, source_path: str, content: str, session_id: str = "", project_id: str = "") -> None:
    async def _ingest() -> None:
        from uuid import UUID

        async for session in get_db():
            pipeline = ProcessingPipeline(session)
            result = await pipeline.process_ingest_request(
                UUID(user_id),
                IngestRequest(
                    source_path=source_path,
                    content=content,
                    session_id=session_id or None,
                    project_id=project_id or None,
                ),
            )
            typer.echo(str(result))

    asyncio.run(_ingest())


@app.command()
def recall(user_id: str, query: str) -> None:
    async def _recall() -> None:
        from uuid import UUID

        async for session in get_db():
            result = await RetrievalService(session).recall(UUID(user_id), query)
            typer.echo(result.model_dump_json(indent=2))

    asyncio.run(_recall())


@app.command()
def reindex(user_id: str, provider: str, model: str, version: str) -> None:
    async def _reindex() -> None:
        from uuid import UUID

        async for session in get_db():
            await ProcessingPipeline(session).reindex_embeddings(UUID(user_id), provider, model, version)
            typer.echo("Reindex complete.")

    asyncio.run(_reindex())


@app.command()
def rebuild(user_id: str) -> None:
    async def _rebuild() -> None:
        from uuid import UUID

        async for session in get_db():
            await ProcessingPipeline(session).rebuild_graph(UUID(user_id))
            typer.echo("Rebuild complete.")

    asyncio.run(_rebuild())


if __name__ == "__main__":
    app()