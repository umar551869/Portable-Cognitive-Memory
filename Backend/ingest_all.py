"""
Master Ingestion Script
=======================
Feeds ALL sources into the Portable Cognitive Graph:
  1. detailed_history.txt   (personal cognitive history)
  2. Starters Data.txt      (starter knowledge)
  3. F:\\Mitigating AI Halucination  (FYP source code & docs)
  4. F:\programming          (all programming projects - source only)

Skips: node_modules, .git, __pycache__, .next, venv, binary files,
       images, datasets (.pt, .jpg, .png, .dll, .exe, .mat, etc.)
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

ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")

# Extensions we CAN read and ingest
INGESTABLE_EXTENSIONS = {
    # Code
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".rb", ".rs", ".go", ".kt", ".scala", ".php", ".lua", ".swift",
    ".sql", ".sh", ".bat", ".ps1", ".f90", ".f95",
    # Web
    ".html", ".htm", ".css", ".scss", ".sass",
    # Config/Docs
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".env",
    ".md", ".txt", ".rst", ".csv",
    # Notebooks (read as text)
    ".ipynb",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".next", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache", ".tox", "eggs", ".eggs",
    "site-packages", ".mypy_cache", ".pytest_cache",
}

# Max file size to ingest (500KB - skip huge generated files)
MAX_FILE_SIZE = 500_000


def should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".")


def collect_files(root_dir: str) -> list[Path]:
    """Collect all ingestable files from a directory tree."""
    files = []
    root = Path(root_dir)
    if not root.exists():
        print(f"  WARNING: {root_dir} does not exist, skipping.")
        return files

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune directories in-place
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()

            if ext not in INGESTABLE_EXTENSIONS:
                continue
            if fpath.stat().st_size > MAX_FILE_SIZE:
                continue
            if fpath.stat().st_size < 50:  # Skip near-empty files
                continue

            files.append(fpath)

    return files


async def ingest_text_segments(segments: list[tuple[str, str]], project_id: str):
    """Ingest a list of (label, content) text segments."""
    total = len(segments)
    success = 0
    for i, (label, content) in enumerate(segments, 1):
        print(f"  [{i}/{total}] {label} ({len(content)} chars)...", end=" ", flush=True)
        async for session in get_db():
            pipeline = ProcessingPipeline(session)
            request = IngestRequest(
                source_path=f"text://{label}",
                content=content,
                session_id="master-ingest",
                project_id=project_id,
            )
            try:
                result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
                print(f"OK ({result})", flush=True)
                success += 1
            except Exception as e:
                print(f"FAIL: {e}", flush=True)
            break
    return success


async def ingest_files(files: list[Path], project_id: str):
    """Ingest a list of source code files."""
    total = len(files)
    success = 0
    for i, fpath in enumerate(files, 1):
        print(f"  [{i}/{total}] {fpath.name} ({fpath.stat().st_size} bytes)...", end=" ", flush=True)
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            if len(content.strip()) < 30:
                print("SKIP (too small)", flush=True)
                continue
        except Exception as e:
            print(f"READ_FAIL: {e}", flush=True)
            continue

        async for session in get_db():
            pipeline = ProcessingPipeline(session)
            request = IngestRequest(
                source_path=str(fpath),
                content=content,
                session_id="master-ingest",
                project_id=project_id,
            )
            try:
                result = await pipeline.process_ingest_request(ADMIN_USER_ID, request)
                print(f"OK ({result})", flush=True)
                success += 1
            except Exception as e:
                print(f"FAIL: {e}", flush=True)
            break
    return success


async def main():
    start = time.time()
    total_success = 0

    # ──────────────────────────────────────────────────────────
    # SOURCE 1: Personal Cognitive History
    # ──────────────────────────────────────────────────────────
    print("=" * 70)
    print("SOURCE 1: Personal Cognitive History (detailed_history.txt)")
    print("=" * 70)
    history_file = Path("detailed_history.txt")
    if history_file.exists():
        content = history_file.read_text(encoding="utf-8")
        segments = re.split(r"---\s*LOG SEGMENT \d+:.*?---", content)
        segments = [(f"history_segment_{i}", s.strip()) for i, s in enumerate(segments, 1) if s.strip()]
        total_success += await ingest_text_segments(segments, "personal-history")
    else:
        print("  File not found, skipping.")

    # ──────────────────────────────────────────────────────────
    # SOURCE 2: Starters Data
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SOURCE 2: Starters Data")
    print("=" * 70)
    starters_file = Path("Starters Data.txt")
    if starters_file.exists():
        content = starters_file.read_text(encoding="utf-8")
        # Split into ~2000 char chunks for better extraction
        chunk_size = 2000
        chunks = []
        for j in range(0, len(content), chunk_size):
            chunk = content[j:j + chunk_size].strip()
            if len(chunk) > 50:
                chunks.append((f"starters_chunk_{j // chunk_size + 1}", chunk))
        total_success += await ingest_text_segments(chunks, "starters-data")
    else:
        print("  File not found, skipping.")

    # ──────────────────────────────────────────────────────────
    # SOURCE 3: Mitigating AI Hallucination (FYP)
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SOURCE 3: Mitigating AI Hallucination Project")
    print("=" * 70)
    fyp_files = collect_files(r"F:\Mitigating AI Halucination")
    print(f"  Found {len(fyp_files)} ingestable files.")
    total_success += await ingest_files(fyp_files, "mitigating-ai-hallucination")

    # ──────────────────────────────────────────────────────────
    # SOURCE 4: Programming Projects
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SOURCE 4: Programming Projects")
    print("=" * 70)
    prog_files = collect_files(r"F:\programming")
    print(f"  Found {len(prog_files)} ingestable files.")
    # Limit to first 500 most important files (by extension priority)
    priority_order = [".py", ".tsx", ".ts", ".jsx", ".js", ".java", ".cpp", ".c",
                      ".sql", ".md", ".txt", ".json", ".cs", ".h", ".hpp"]
    def sort_key(f):
        ext = f.suffix.lower()
        try:
            return priority_order.index(ext)
        except ValueError:
            return 100
    prog_files.sort(key=sort_key)
    if len(prog_files) > 500:
        print(f"  Limiting to top 500 priority files (from {len(prog_files)} total).")
        prog_files = prog_files[:500]
    total_success += await ingest_files(prog_files, "programming-projects")

    # ──────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────
    elapsed = time.time() - start
    print("\n" + "=" * 70)
    print(f"MASTER INGESTION COMPLETE")
    print(f"  Total files/segments ingested: {total_success}")
    print(f"  Elapsed time: {elapsed / 60:.1f} minutes")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
