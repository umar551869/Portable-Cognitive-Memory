from __future__ import annotations
import asyncio
from uuid import UUID
from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest

async def main() -> None:
    ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")
    async for session in get_db():
        pipeline = ProcessingPipeline(session)
        request = IngestRequest(
            source_path="test_mini.txt",
            content="Stability is achieved through Gradient Penalty (WGAN-GP).",
            session_id="mini-test",
            project_id="test",
        )
        print("Starting mini ingestion...")
        result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
        print(f"Success: {result}")
        break

if __name__ == "__main__":
    asyncio.run(main())
