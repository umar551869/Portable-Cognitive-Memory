import asyncio
from sqlalchemy import select
from pcg.storage.db import get_db
from pcg.storage.models import Node, Edge

async def list_data():
    async for session in get_db():
        nodes = (await session.scalars(select(Node))).all()
        edges = (await session.scalars(select(Edge))).all()
        print("--- NODES ---")
        for n in nodes:
            print(f"[{n.id}] [{n.type}] {n.canonical_name} (aliases: {n.aliases})")
        print("--- EDGES ---")
        for e in edges:
            print(f"{e.source_id} --({e.relation})--> {e.target_id}")
        break

if __name__ == "__main__":
    asyncio.run(list_data())
