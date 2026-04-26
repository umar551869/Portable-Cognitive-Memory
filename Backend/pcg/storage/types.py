from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator


class PortableVector(TypeDecorator):
    """Store vectors as JSON across PostgreSQL and SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Sequence[float] | None, dialect) -> Any:
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value: Any, dialect) -> list[float] | None:
        if value is None:
            return None
        return [float(item) for item in value]
