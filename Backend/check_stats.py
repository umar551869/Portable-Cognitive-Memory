import asyncio
from sqlalchemy import select, func
from pcg.storage.db import get_db
from pcg.storage.models import Node, Edge

async def check_stats():
    async for session in get_db():
        node_count = await session.scalar(select(func.count(Node.id)))
        edge_count = await session.scalar(select(func.count(Edge.id)))
        print(f"Total Nodes: {node_count}")
        print(f"Total Edges: {edge_count}")
        
        print("\n--- Recent Nodes ---")
        nodes = (await session.scalars(select(Node).limit(20))).all()
        for n in nodes:
            print(f"[{n.type}] {n.canonical_name}")
        break

if __name__ == "__main__":
    asyncio.run(check_stats())
