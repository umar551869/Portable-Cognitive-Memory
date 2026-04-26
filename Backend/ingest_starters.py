from __future__ import annotations

import asyncio
import os
from uuid import uuid4

from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest


async def main() -> None:
    # Use a fixed test user ID for consistency
    TEST_USER_ID = uuid4()
    
    # Read Starters Data.txt
    file_path = "Starters Data.txt"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"Ingesting content from {file_path}...")
    print(f"Content: {content[:100]}...")

    async for session in get_db():
        pipeline = ProcessingPipeline(session)
        
        request = IngestRequest(
            source_path=file_path,
            content=content,
            session_id="starters-ingestion",
            project_id="pcg-project",
        )
        
        try:
            result = await pipeline.process_ingest_request(TEST_USER_ID, request)
            print("-" * 30)
            print("INGESTION SUCCESSFUL")
            print(f"Chunks: {result.chunk_count}")
            print(f"Nodes: {result.node_count}")
            print(f"Edges: {result.edge_count}")
            print("-" * 30)
        except Exception as e:
            print(f"Pipeline Failed: {e}")
        break


if __name__ == "__main__":
    asyncio.run(main())
