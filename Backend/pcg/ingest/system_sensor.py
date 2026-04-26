from __future__ import annotations
import asyncio
import os
import time
from pathlib import Path
from uuid import UUID
from pcg.processing.pipeline import ProcessingPipeline
from pcg.storage.db import get_db
from pcg.utils.schemas import IngestRequest

class SystemSensor:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.history_file = Path(os.environ["APPDATA"]) / "Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
        self.last_size = 0
        if self.history_file.exists():
            self.last_size = self.history_file.stat().st_size

    async def monitor(self):
        print(f"Monitoring system logs (CLI history) for user {self.user_id}...", flush=True)
        print(f"Watching: {self.history_file}", flush=True)
        
        while True:
            try:
                if not self.history_file.exists():
                    await asyncio.sleep(10)
                    continue

                current_size = self.history_file.stat().st_size
                if current_size > self.last_size:
                    with open(self.history_file, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(self.last_size)
                        new_content = f.read().strip()
                        if new_content:
                            await self._ingest_content(new_content)
                    self.last_size = current_size
                elif current_size < self.last_size:
                    # File was cleared or rotated
                    self.last_size = current_size
            except Exception as e:
                print(f"Sensor Error: {e}")
            
            await asyncio.sleep(5)

    async def _ingest_content(self, content: str):
        print(f"New CLI Activity detected: {len(content)} chars", flush=True)
        async for session in get_db():
            pipeline = ProcessingPipeline(session)
            request = IngestRequest(
                source_path="system://cli_history",
                content=content,
                session_id="system-sensor",
                project_id="os-context",
            )
            try:
                await pipeline.process_ingest_request(self.user_id, request)
                print("  Successfully integrated into Cognitive Memory.", flush=True)
            except Exception as e:
                print(f"  Ingestion Failed: {e}", flush=True)
            break

async def main():
    # Muhammad Umar Ilyas
    ADMIN_USER_ID = UUID("085f208a-c50a-4ebf-b389-cf882addc374")
    sensor = SystemSensor(ADMIN_USER_ID)
    await sensor.monitor()

if __name__ == "__main__":
    asyncio.run(main())
