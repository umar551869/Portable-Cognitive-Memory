"""Ingest detailed_history.txt into the PCG in segments."""
import asyncio, re
from uuid import UUID
from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest

ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")
SOURCE_FILE = "detailed_history.txt"

async def main():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by LOG SEGMENT markers
    segments = re.split(r"---\s*LOG SEGMENT \d+:.*?---", content)
    segments = [s.strip() for s in segments if s.strip()]

    print(f"Found {len(segments)} segments to ingest.")

    total_nodes = 0
    total_edges = 0

    for i, segment in enumerate(segments, 1):
        print(f"\n{'='*60}")
        print(f"SEGMENT {i}/{len(segments)} ({len(segment)} chars)")
        print(f"{'='*60}")
        async for session in get_db():
            pipeline = ProcessingPipeline(session)
            request = IngestRequest(
                source_path=f"history://segment_{i}",
                content=segment,
                session_id="history-ingest",
                project_id="personal-history",
            )
            try:
                result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
                print(f"  Result: {result}")
                total_nodes += getattr(result, 'node_count', 0)
                total_edges += getattr(result, 'edge_count', 0)
            except Exception as e:
                print(f"  ERROR: {e}")
            break

    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"Total nodes created: {total_nodes}")
    print(f"Total edges created: {total_edges}")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
