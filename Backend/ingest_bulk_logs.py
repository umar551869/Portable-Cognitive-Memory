from __future__ import annotations
import asyncio
import os
from uuid import UUID
from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest

async def main() -> None:
    # User ID for Muhammad Umar Ilyas
    ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")
    
    file_path = "Starters Data.txt"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
    
    # Split by the separator I recommended in the prompt
    logs = full_content.split("---NEW_LOG---")
    
    print(f"Found {len(logs)} logs to ingest.")

    async for session in get_db():
        pipeline = ProcessingPipeline(session)
        
        for i, log_content in enumerate(logs):
            content = log_content.strip()
            if not content:
                continue
                
            # Try to find a title in the first line
            lines = content.split("\n")
            title = lines[0].strip() if lines else f"Log {i}"
            
            print(f"Ingesting: {title[:50]}...")
            
            request = IngestRequest(
                source_path=f"starters_data/log_{i}.txt",
                content=content,
                session_id="starters-bulk-ingestion",
                project_id="pcg-project",
            )
            
            try:
                result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
                print(f"  SUCCESS: Chunks={result.chunk_count}, Nodes={result.node_count}, Edges={result.edge_count}")
            except Exception as e:
                print(f"  FAILED: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(main())
