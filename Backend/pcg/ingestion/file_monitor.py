from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Iterable, List, Set
from uuid import UUID

import psutil
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from pcg.processing.pipeline import ProcessingPipeline
from pcg.utils.logging import get_logger


logger = get_logger("ingestion.monitor")
PENDING_FILE = ".pcg_pending.json"


class PCGFileEventHandler(FileSystemEventHandler):
    """Queue file changes and process them in power-aware batches."""

    def __init__(self, user_id: UUID, supported_extensions: Iterable[str], pipeline: ProcessingPipeline | None = None):
        self.user_id = user_id
        self.supported_extensions = {value.lower() for value in supported_extensions}
        self.pipeline = pipeline or ProcessingPipeline()
        self.loop = asyncio.get_running_loop()
        self.pending_files = self._load_pending_files()
        self.last_push_time = self.loop.time()
        self.push_interval_seconds = 300 # 5 minutes for more active updates
        self.is_running = True
        self.loop.create_task(self._maintenance_loop())

    def _load_pending_files(self) -> Set[str]:
        pending_path = Path(PENDING_FILE)
        if not pending_path.exists():
            return set()
        try:
            payload = json.loads(pending_path.read_text(encoding="utf-8"))
            return {str(Path(item)) for item in payload}
        except Exception as exc:  # noqa: BLE001
            logger.warning("pending_file_load_failed error=%s", exc)
            return set()

    def _save_pending_files(self) -> None:
        try:
            Path(PENDING_FILE).write_text(json.dumps(sorted(self.pending_files), indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning("pending_file_save_failed error=%s", exc)

    @staticmethod
    def _is_plugged_in() -> bool:
        battery = psutil.sensors_battery()
        if battery is None:
            return True
        return bool(battery.power_plugged)

    async def _process_batch(self, user_id: UUID) -> None:
        if not self.pending_files:
            return

        if not self._is_plugged_in():
            logger.info("batch_deferred_on_battery pending_count=%s", len(self.pending_files))
            return

        pending = sorted(self.pending_files)
        self.pending_files.clear()
        self._save_pending_files()
        logger.info("batch_start pending_count=%s", len(pending))

        from pcg.utils.schemas import IngestRequest
        
        for file_path in pending:
            p = Path(file_path)
            if not p.exists():
                logger.info("skipping_deleted_file path=%s", file_path)
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if len(content.strip()) < 50: continue
                
                req = IngestRequest(
                    source_path=file_path,
                    content=content,
                    project_id="background_monitor"
                )
                await self.pipeline.process_ingest_request(user_id, req)
            except Exception as exc:  # noqa: BLE001
                logger.exception("file_processing_failed path=%s error=%s", file_path, exc)
                self.pending_files.add(file_path)
                self._save_pending_files()

        logger.info("batch_complete remaining_pending=%s", len(self.pending_files))

    async def _maintenance_loop(self) -> None:
        was_unplugged = not self._is_plugged_in()
        while self.is_running:
            await asyncio.sleep(60)
            is_plugged = self._is_plugged_in()
            current_time = self.loop.time()
            if is_plugged and was_unplugged:
                logger.info("power_reconnected_processing_backlog")
                await self._process_batch(self.user_id)
                self.last_push_time = current_time
            elif is_plugged and current_time - self.last_push_time >= self.push_interval_seconds:
                await self._process_batch(self.user_id)
                self.last_push_time = current_time
            was_unplugged = not is_plugged

    def _track_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in self.supported_extensions:
            return
        self.pending_files.add(str(path))
        self._save_pending_files()
        logger.info("file_tracked path=%s", path)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._track_event(event)

    def on_created(self, event: FileSystemEvent) -> None:
        self._track_event(event)


async def start_file_monitor(user_id: UUID, path: str, extensions: List[str]) -> None:
    observer = Observer()
    event_handler = PCGFileEventHandler(user_id, extensions)
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logger.info("monitor_started path=%s user_id=%s", path, user_id)
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("monitor_cancelled path=%s", path)
        raise
    finally:
        event_handler.is_running = False
        observer.stop()
        observer.join()
