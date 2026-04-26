import asyncio
from sqlalchemy import delete
from pcg.storage.db import get_db
from pcg.storage.models import Node, Edge

async def cleanup():
    async for session in get_db():
        await session.execute(delete(Node))
        await session.execute(delete(Edge))
        await session.commit()
        print("Database cleared.")
        break

if __name__ == "__main__":
    asyncio.run(cleanup())
