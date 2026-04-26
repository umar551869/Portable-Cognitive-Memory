from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field


NodeType = Literal["concept", "process", "mechanism", "decision", "unknown"]
EmbeddingOwnerType = Literal["node", "chunk"]


class EntityCandidate(BaseModel):
    temp_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: NodeType = "unknown"
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipCandidate(BaseModel):
    source_name: str
    target_name: str
    relation: str
    weight: float = 1.0
    evidence: Optional[str] = None


class EntityExtractionResult(BaseModel):
    entities: List[EntityCandidate] = Field(default_factory=list)


class RelationshipExtractionResult(BaseModel):
    relationships: List[RelationshipCandidate] = Field(default_factory=list)


class RawLog(BaseModel):
    id: UUID
    user_id: UUID
    source_path: str
    content: str
    content_hash: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    file_modified_at: Optional[datetime] = None


class ContentChunk(BaseModel):
    id: UUID
    raw_log_id: UUID
    user_id: UUID
    ordinal: int
    content: str
    content_hash: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResolvedNode(BaseModel):
    id: UUID
    user_id: UUID
    canonical_name: str
    display_name: str
    type: NodeType = "unknown"
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    weight: int = 1


class EdgeRecord(BaseModel):
    source_id: UUID
    target_id: UUID
    relation: str
    user_id: UUID
    weight: int = 1
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    evidence: Optional[str] = None


class EmbeddingRecord(BaseModel):
    id: UUID
    owner_type: EmbeddingOwnerType
    user_id: UUID
    content: str
    embedding: List[float]
    embedding_model: str
    embedding_version: str
    node_id: Optional[UUID] = None
    chunk_id: Optional[UUID] = None
    raw_log_id: Optional[UUID] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphStats(BaseModel):
    node_count: int = 0
    edge_count: int = 0
    embedding_count: int = 0
    raw_log_count: int = 0
    chunk_count: int = 0


class RetrievalNode(BaseModel):
    id: UUID
    canonical_name: str
    display_name: str
    type: NodeType = "unknown"
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    weight: int = 1
    score: float = 0.0


class RetrievalEdge(BaseModel):
    source_id: UUID
    target_id: UUID
    relation: str
    weight: int = 1
    evidence: Optional[str] = None


class RetrievalRawLog(BaseModel):
    id: UUID
    source_path: str
    excerpt: str
    score: float = 0.0


class RecallResult(BaseModel):
    query: str
    nodes: List[RetrievalNode] = Field(default_factory=list)
    edges: List[RetrievalEdge] = Field(default_factory=list)
    raw_logs: List[RetrievalRawLog] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    is_admin: bool
    created_at: datetime


class IngestRequest(BaseModel):
    source_path: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    session_id: Optional[str] = Field(default=None, max_length=128)
    project_id: Optional[str] = Field(default=None, max_length=128)


class IngestResponse(BaseModel):
    raw_log_id: UUID
    status: str


class ReindexRequest(BaseModel):
    provider: Literal["openai", "gemini", "local"]
    model: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)


class RebuildResponse(BaseModel):
    status: str


class GraphResponse(BaseModel):
    nodes: List[RetrievalNode]
    edges: List[RetrievalEdge]


class IngestDirectoryRequest(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    project_id: str = Field(default="bulk-import", max_length=128)
