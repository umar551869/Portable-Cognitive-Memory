import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from pcg.storage.db import get_db
from pcg.storage.models import RawLog

async def check_new_logs():
    async for session in get_db():
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        stmt = select(RawLog).where(RawLog.created_at >= one_minute_ago)
        logs = (await session.scalars(stmt)).all()
        print(f"New logs in last 5 mins: {len(logs)}")
        for l in logs:
            print(f"- {l.source_path}")
        break

if __name__ == "__main__":
    asyncio.run(check_new_logs())
