import os
import asyncio
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import List

from pcg.config.settings import settings
from pcg.utils.db import get_db, AsyncSessionLocal
from pcg.utils.schemas import RawLog
from pcg.memory.repository import MemoryRepository
from pcg.processing.pipeline import process_raw_log # Now imported

class PCGFileEventHandler(FileSystemEventHandler):
    def __init__(self, supported_extensions: List[str]):
        self.supported_extensions = supported_extensions

    def _is_supported_file(self, file_path: str) -> bool:
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.supported_extensions

    async def _handle_file(self, event_path: str):
        if not self._is_supported_file(event_path):
            return

        if not os.path.exists(event_path):
            # File might have been deleted before we could read it
            return

        print(f"Detected change in supported file: {event_path}")
        try:
            with open(event_path, 'r', encoding='utf-8') as f:
                content = f.read()

            raw_log_id = str(uuid.uuid5(uuid.NAMESPACE_URL, event_path + content)) # Unique ID for the raw log
            raw_log = RawLog(id=raw_log_id, source_path=event_path, content=content)

            # Use a new session for each event to avoid issues with concurrent access
            async for db_session in get_db():
                repo = MemoryRepository(db_session)
                await repo.add_raw_log(raw_log)
                print(f"Stored raw log for {event_path}")
                await process_raw_log(raw_log) # Now call the processing pipeline

        except Exception as e:
            print(f"Error processing file {event_path}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            # Run in a separate task to avoid blocking the watchdog observer
            asyncio.create_task(self._handle_file(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            # Run in a separate task to avoid blocking the watchdog observer
            asyncio.create_task(self._handle_file(event.src_path))

async def start_file_monitor(path: str, extensions: List[str]):
    """Starts monitoring a directory for file changes."""
    print(f"Starting file monitor for directory: {path} with extensions: {extensions}")
    event_handler = PCGFileEventHandler(supported_extensions=extensions)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        # Keep the observer running indefinitely, or until stopped
        while True:
            await asyncio.sleep(1) # Small sleep to yield control
    except asyncio.CancelledError:
        print(f"Monitoring for {path} was cancelled.")
    finally:
        observer.stop()
        observer.join()
        print(f"Stopped monitoring directory: {path}")

async def stop_file_monitor(observer: Observer):
    """Stops the file monitor."""
    if observer.is_alive():
        observer.stop()
        observer.join()
        print("File monitor stopped.")
