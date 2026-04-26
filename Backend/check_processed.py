import asyncio
from sqlalchemy import select
from pcg.storage.db import get_db
from pcg.storage.models import RawLog

async def check_processed():
    async for session in get_db():
        logs = (await session.scalars(select(RawLog).where(RawLog.processed_at != None).order_by(RawLog.processed_at.desc()))).all()
        print("--- RECENTLY PROCESSED ---")
        for l in logs[:10]:
            print(f"[{l.processed_at}] {l.source_path}")
        break

if __name__ == "__main__":
    asyncio.run(check_processed())
