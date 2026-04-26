from __future__ import annotations

import hashlib
import re
from typing import List
from uuid import UUID, uuid5, NAMESPACE_URL

from pcg.config.settings import settings
from pcg.utils.schemas import ContentChunk


_MARKDOWN_HEADING_PATTERN = re.compile(r"(^#+\s+.*$)", re.MULTILINE)
_PYTHON_BLOCK_PATTERN = re.compile(r"(^\s*(?:class|def)\s+.+?:)", re.MULTILINE)


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _approximate_split(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - chunk_overlap)
    return [chunk for chunk in chunks if chunk]


def _split_by_markdown_headings(text: str) -> List[str]:
    matches = list(_MARKDOWN_HEADING_PATTERN.finditer(text))
    if not matches:
        return []
    sections: List[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        if value:
            sections.append(value)
    return sections


def _split_python_blocks(text: str) -> List[str]:
    matches = list(_PYTHON_BLOCK_PATTERN.finditer(text))
    if not matches:
        return []
    sections: List[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        if value:
            sections.append(value)
    return sections


def build_chunks(
    *,
    raw_log_id: UUID,
    user_id: UUID,
    source_path: str,
    content: str,
    session_id: str | None,
    project_id: str | None,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> list[ContentChunk]:
    strategy = "approximate"
    if source_path.lower().endswith(".md") or _MARKDOWN_HEADING_PATTERN.search(content):
        units = _split_by_markdown_headings(content)
        strategy = "markdown"
    elif source_path.lower().endswith((".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs")):
        units = _split_python_blocks(content)
        strategy = "code"
    else:
        units = []
    if not units:
        units = _approximate_split(content, chunk_size, chunk_overlap)

    chunks: list[ContentChunk] = []
    for ordinal, unit in enumerate(units or [content]):
        content_hash = _content_hash(unit)
        chunks.append(
            ContentChunk(
                id=uuid5(NAMESPACE_URL, f"{raw_log_id}:{ordinal}:{content_hash}"),
                raw_log_id=raw_log_id,
                user_id=user_id,
                ordinal=ordinal,
                content=unit,
                content_hash=content_hash,
                session_id=session_id,
                project_id=project_id,
                metadata={"source_path": source_path, "strategy": strategy},
            )
        )
    return chunks
