"""
Hybrid Master Ingestion Script
==============================
Feeds ALL sources into the Portable Cognitive Graph with smart fallback:
  - Tries Gemini API first (High Speed)
  - If 429/Quota hit, falls back to Local Ollama (Reliable)
  - Gradually works through all history, FYP, and programming projects.
"""
import asyncio
import os
import re
import sys
import time
from pathlib import Path
from uuid import UUID

# Ensure pcg is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest
from pcg.config.settings import settings

ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")

INGESTABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".rb", ".rs", ".go", ".kt", ".sql", ".sh", ".md", ".txt", ".json",
    ".yml", ".yaml", ".env", ".html", ".css", ".ipynb"
}

SKIP_DIRS = {
    "node_modules", ".git", ".next", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache"
}

MAX_FILE_SIZE = 300_000 # 300KB limit for bulk

def collect_files(root_dir: str) -> list[Path]:
    files = []
    root = Path(root_dir)
    if not root.exists(): return files
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            try:
                if fpath.suffix.lower() in INGESTABLE_EXTENSIONS and fpath.stat().st_size < MAX_FILE_SIZE:
                    files.append(fpath)
            except Exception: continue
    return files

from pcg.providers.factory import get_provider

async def process_with_fallback(pipeline, request, label):
    """Call pipeline; internal fallback (Gemini -> OpenAI) is now handled by settings."""
    try:
        result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
        print(f"  OK -> {result}")
        return result
    except Exception as e:
        print(f"  [ERROR] Ingestion failed for: {label} (Error: {e})")
        return None

async def main():
    print("=" * 80)
    print("HYBRID INGESTION ENGINE (v2) STARTING")
    print(f"Providers: Gemini -> OpenAI -> Local (Ollama)")
    print("=" * 80)

    async for session in get_db():
        pipeline = ProcessingPipeline(session)

        # 1. Starters Data
        starters_file = Path("Starters Data.txt")
        if starters_file.exists():
            print(f"\n>> Processing Starters Data: {starters_file.absolute()}")
            content = starters_file.read_text(encoding="utf-8")
            # Chunking for reliable extraction
            chunk_size = 2200
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            print(f"   Split into {len(chunks)} chunks.")
            for i, chunk in enumerate(chunks, 1):
                req = IngestRequest(source_path=f"text://starters_chunk_{i}", content=chunk.strip(), project_id="starters")
                print(f"  [Chunk {i}/{len(chunks)}]", end="")
                await process_with_fallback(pipeline, req, f"Starters Chunk {i}")
        else:
            print(f"\n>> Starters file not found.")

        # 2. History
        history_file = Path("detailed_history.txt")
        if history_file.exists():
            print(f"\n>> Processing History: {history_file.absolute()}")
            content = history_file.read_text(encoding="utf-8")
            segments = [s for s in re.split(r"---\s*LOG SEGMENT \d+:.*?---", content) if s.strip()]
            print(f"   Found {len(segments)} segments.")
            for i, seg in enumerate(segments, 1):
                req = IngestRequest(source_path=f"history://seg_{i}", content=seg.strip(), project_id="history")
                print(f"  [Seg {i}/{len(segments)}]", end="")
                await process_with_fallback(pipeline, req, f"History Seg {i}")
        else:
            print(f"\n>> History file not found.")

        # 3. FYP Project
        fyp_path = r"F:\Mitigating AI Halucination"
        print(f"\n>> Processing FYP: {fyp_path}")
        if Path(fyp_path).exists():
            fyp_files = collect_files(fyp_path)
            print(f"   Found {len(fyp_files)} files.")
            for i, f in enumerate(fyp_files, 1):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if len(content.strip()) < 50: continue
                    req = IngestRequest(source_path=str(f), content=content, project_id="fyp")
                    print(f"  [{i}/{len(fyp_files)}] {f.name}...", end="")
                    await process_with_fallback(pipeline, req, f.name)
                except Exception as e: print(f"SKIP {f.name}: {e}")
        else:
            print("   ERROR: FYP path not found. Skipping.")

        # 4. Programming Projects (Capped)
        prog_path = r"F:\programming"
        print(f"\n>> Processing Programming: {prog_path}")
        if Path(prog_path).exists():
            prog_files = collect_files(prog_path)
            prog_files.sort(key=lambda x: x.suffix) # Group by type
            limit = 500
            print(f"   Found {len(prog_files)} files. Capping at {limit}.")
            for i, f in enumerate(prog_files[:limit], 1):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if len(content.strip()) < 100: continue
                    req = IngestRequest(source_path=str(f), content=content, project_id="programming")
                    print(f"  [{i}/{limit}] {f.name}...", end="")
                    await process_with_fallback(pipeline, req, f.name)
                except Exception as e: print(f"SKIP {f.name}: {e}")
        else:
            print("   ERROR: Programming path not found. Skipping.")
        
        print("\n" + "=" * 80)
        print("HYBRID INGESTION COMPLETE")
        print("=" * 80)
        break

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
