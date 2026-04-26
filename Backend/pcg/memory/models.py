from sqlalchemy import Column, Integer, String, JSON, DateTime, text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Node(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False, index=True)
    canonical_name = Column(String, nullable=False, index=True)
    aliases = Column(JSONB, default=text("'[]'::jsonb"))
    weight = Column(Integer, default=1)
    metadata = Column(JSONB, default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    embeddings = relationship("Embedding", back_populates="node", cascade="all, delete-orphan")
    source_edges = relationship("Edge", foreign_keys="[Edge.source]", back_populates="source_node", cascade="all, delete-orphan")
    target_edges = relationship("Edge", foreign_keys="[Edge.target]", back_populates="target_node", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Node(id='{self.id}', type='{self.type}', canonical_name='{self.canonical_name}')>"

class Edge(Base):
    __tablename__ = "edges"

    id = Column(String, primary_key=True)
    source = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    relation = Column(String, nullable=False, index=True)
    weight = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source_node = relationship("Node", foreign_keys="[Edge.source]", back_populates="source_edges")
    target_node = relationship("Node", foreign_keys="[Edge.target]", back_populates="target_edges")

    def __repr__(self):
        return f"<Edge(id='{self.id}', source='{self.source}', target='{self.target}', relation='{self.relation}')>"

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String, primary_key=True)
    node_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    node = relationship("Node", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id='{self.id}', node_id='{self.node_id}', content='{self.content[:30]}...')>"

class RawLog(Base):
    __tablename__ = "raw_logs"

    id = Column(String, primary_key=True)
    source_path = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<RawLog(id='{self.id}', source_path='{self.source_path}')>"