from __future__ import annotations

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from pcg.storage.types import PortableVector

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("user_id", "canonical_name", name="uq_nodes_user_canonical_name"),
        Index("ix_nodes_user_canonical_name", "user_id", "canonical_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    canonical_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="unknown")
    aliases = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    weight = Column(Integer, nullable=False, default=1)
    session_id = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RawLog(Base):
    __tablename__ = "raw_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "content_hash", name="uq_raw_logs_user_content_hash"),
        Index("ix_raw_logs_user_source_path", "user_id", "source_path"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    session_id = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    file_modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("raw_log_id", "ordinal", name="uq_chunks_raw_log_ordinal"),
        Index("ix_chunks_user_raw_log", "user_id", "raw_log_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_log_id = Column(UUID(as_uuid=True), ForeignKey("raw_logs.id", ondelete="CASCADE"), nullable=False)
    ordinal = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    session_id = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Edge(Base):
    __tablename__ = "edges"
    __table_args__ = (
        UniqueConstraint("user_id", "source_id", "target_id", "relation", name="uq_edges_user_triplet"),
        Index("ix_edges_user_source_target", "user_id", "source_id", "target_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    relation = Column(String, nullable=False)
    weight = Column(Integer, nullable=False, default=1)
    evidence = Column(Text, nullable=True)
    session_id = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        Index("ix_embeddings_user_owner_type", "user_id", "owner_type"),
        Index("ix_embeddings_user_model_version", "user_id", "embedding_model", "embedding_version"),
        Index("ix_embeddings_user_node", "user_id", "node_id"),
        Index("ix_embeddings_user_chunk", "user_id", "chunk_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_type = Column(String, nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=True)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=True)
    raw_log_id = Column(UUID(as_uuid=True), ForeignKey("raw_logs.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(PortableVector(), nullable=False)
    embedding_model = Column(String, nullable=False)
    embedding_version = Column(String, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    session_id = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
