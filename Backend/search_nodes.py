import asyncio
from sqlalchemy import select
from pcg.storage.db import get_db
from pcg.storage.models import Node

async def search_nodes():
    async for session in get_db():
        nodes = (await session.scalars(select(Node).where(Node.canonical_name.like("%Umar%")))).all()
        print(f"Found {len(nodes)} nodes with 'Umar':")
        for n in nodes:
            print(f"[{n.id}] {n.canonical_name}")
        
        nodes_jarvis = (await session.scalars(select(Node).where(Node.canonical_name.like("%Jarvis%")))).all()
        print(f"\nFound {len(nodes_jarvis)} nodes with 'Jarvis':")
        for n in nodes_jarvis:
            print(f"[{n.id}] {n.canonical_name}")
        break

if __name__ == "__main__":
    asyncio.run(search_nodes())
