import asyncio
import sys
import os
from uuid import UUID
from pathlib import Path

# Ensure pcg is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcg.ingestion.system_discovery import DiscoveryService
from pcg.ingestion.file_monitor import start_file_monitor
from pcg.storage.db import get_session_factory
from pcg.processing.pipeline import ProcessingPipeline
from pcg.utils.schemas import IngestRequest

ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")

async def initial_ingest(user_id: UUID, paths: list[Path]):
    """One-time ingestion of discovered paths."""
    print(f"\n>> Starting Initial Ingestion for {len(paths)} locations...")
    
    INGESTABLE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".sql", ".sh", ".md", ".txt", ".json", ".yml", ".yaml", ".html", ".css"
    }

    async with get_session_factory()() as session:
        pipeline = ProcessingPipeline(session)
        for path in paths:
            print(f"   Crawling: {path}")
            if path.is_file():
                files = [path]
            else:
                files = []
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = Path(dirpath) / f
                        if fp.suffix.lower() in INGESTABLE_EXTENSIONS:
                            files.append(fp)
            
            print(f"   Found {len(files)} files in {path.name}")
            for i, f in enumerate(files, 1):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if len(content.strip()) < 50: continue
                    req = IngestRequest(source_path=str(f), content=content, project_id=path.name)
                    await pipeline.process_ingest_request(user_id, req)
                    if i % 10 == 0: print(f"      Processed {i}/{len(files)} files...")
                except Exception as e:
                    print(f"      Error processing {f.name}: {e}")

async def main():
    print("=" * 80)
    print("PORTABLE COGNITIVE MEMORY - SYSTEM WATCHER & DISCOVERY")
    print("=" * 80)
    
    # 1. Discovery
    print(">> Discovering starter paths and history...")
    starter_paths = DiscoveryService.get_starter_paths()
    for p in starter_paths:
        print(f"   [+] Found: {p}")
        
    # 2. Initial Ingest (Optional/Incremental)
    await initial_ingest(ADMIN_USER_ID, starter_paths)
    
    # 3. Start Multi-Folder Monitor
    print("\n>> All starters ingested. Engaging background monitoring...")
    print("   Sitting in your system. Monitoring for changes...")
    
    # Supported extensions
    exts = [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".json", ".sql"]
    
    # We monitor each discovered path
    tasks = []
    for path in starter_paths:
        if path.exists():
            tasks.append(start_file_monitor(ADMIN_USER_ID, str(path), exts))
            
    if not tasks:
        print("   ERROR: No paths to monitor. Exiting.")
        return

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n>> Watcher stopped by user. Goodbye Sir.")
