from __future__ import annotations

import asyncio
from uuid import uuid4

from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest


async def main() -> None:
    async for session in get_db():
        pipeline = ProcessingPipeline(session)
        user_id = uuid4()  # Random test user
        
        request = IngestRequest(
            source_path="manual_test.txt",
            content="Project AI-Research is led by Dr. Smith. It focuses on cognitive graphs and memory systems.",
            session_id="manual-test",
            project_id="ai-research",
        )
        
        try:
            result = await pipeline.process_ingest_request(user_id, request)
            print(f"Pipeline Result: {result}")
        except Exception as e:
            print(f"Pipeline Failed: {e}")
        break


if __name__ == "__main__":
    asyncio.run(main())
