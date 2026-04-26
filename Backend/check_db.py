import asyncio
from sqlalchemy import select, func
from pcg.storage.db import get_db
from pcg.storage.models import Node, Edge, Embedding, RawLog

async def check():
    async for session in get_db():
        n_count = await session.scalar(select(func.count()).select_from(Node))
        e_count = await session.scalar(select(func.count()).select_from(Edge))
        emb_count = await session.scalar(select(func.count()).select_from(Embedding))
        log_count = await session.scalar(select(func.count()).select_from(RawLog))
        print(f"Nodes: {n_count}")
        print(f"Edges: {e_count}")
        print(f"Embeddings: {emb_count}")
        print(f"Raw Logs: {log_count}")
        break

if __name__ == "__main__":
    asyncio.run(check())
