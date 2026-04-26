import asyncio
from sqlalchemy import select
from pcg.storage.db import get_db
from pcg.storage.models import RawLog

async def list_sources():
    async for session in get_db():
        sources = (await session.scalars(select(RawLog.source_path).distinct())).all()
        print("--- INGESTED SOURCES ---")
        for s in sorted(sources):
            print(s)
        
        print(f"\nTotal unique sources: {len(sources)}")
        break

if __name__ == "__main__":
    asyncio.run(list_sources())
