from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import uuid
from pgvector.sqlalchemy import Vector

from pcg.config.settings import settings
from pcg.utils.schemas import Node, Edge, Embedding, RawLog, SessionSummary

# Setup SQLAlchemy async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False # Set to True to see SQL statements
)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Database Operations --- (Simplified placeholders)

async def upsert_node(db: AsyncSession, node: Node) -> Node:
    """Inserts or updates a node in the database."""
    # This is a simplified example. In a full implementation, you'd use SQLAlchemy ORM models.
    # For now, we'll use raw SQL with basic upsert logic.
    query = text("""
        INSERT INTO nodes (id, type, canonical_name, aliases, weight, metadata)
        VALUES (:id, :type, :canonical_name, :aliases::jsonb, :weight, :metadata::jsonb)
        ON CONFLICT (id) DO UPDATE SET
            type = EXCLUDED.type,
            canonical_name = EXCLUDED.canonical_name,
            aliases = (nodes.aliases || EXCLUDED.aliases)::jsonb, -- Merge aliases
            weight = nodes.weight + EXCLUDED.weight, -- Increment weight
            metadata = (nodes.metadata || EXCLUDED.metadata)::jsonb -- Merge metadata
        RETURNING *;
    """)
    result = await db.execute(query, {
        "id": node.id,
        "type": node.type,
        "canonical_name": node.canonical_name,
        "aliases": node.aliases.json(), # Convert Pydantic list/dict to JSON string
        "weight": node.weight,
        "metadata": node.metadata.json()
    })
    await db.commit()
    # Re-fetch or reconstruct the updated node (simplified for now)
    return Node(**result.first()._asdict())

async def upsert_edge(db: AsyncSession, edge: Edge) -> Edge:
    """Inserts or updates an edge in the database."""
    edge_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{edge.source}-{edge.relation}-{edge.target}"))
    query = text("""
        INSERT INTO edges (id, source, target, relation, weight)
        VALUES (:id, :source, :target, :relation, :weight)
        ON CONFLICT (id) DO UPDATE SET
            weight = edges.weight + EXCLUDED.weight -- Increment weight
        RETURNING *;
    """)
    result = await db.execute(query, {
        "id": edge_id,
        "source": edge.source,
        "target": edge.target,
        "relation": edge.relation,
        "weight": edge.weight
    })
    await db.commit()
    # Reconstruct the updated edge (simplified)
    return Edge(**result.first()._asdict())

async def add_raw_log(db: AsyncSession, raw_log: RawLog) -> RawLog:
    """Adds a raw log entry to the database."""
    query = text("""
        INSERT INTO raw_logs (id, source_path, content)
        VALUES (:id, :source_path, :content)
        RETURNING *;
    """)
    result = await db.execute(query, {
        "id": raw_log.id,
        "source_path": raw_log.source_path,
        "content": raw_log.content
    })
    await db.commit()
    return RawLog(**result.first()._asdict())

async def add_embedding(db: AsyncSession, embedding_obj: Embedding) -> Embedding:
    """Adds an embedding to the database."""
    query = text("""
        INSERT INTO embeddings (id, node_id, content, embedding)
        VALUES (:id, :node_id, :content, :embedding)
        RETURNING *;
    """)
    result = await db.execute(query, {
        "id": embedding_obj.id,
        "node_id": embedding_obj.node_id,
        "content": embedding_obj.content,
        "embedding": Vector(embedding_obj.embedding)
    })
    await db.commit()
    return Embedding(**result.first()._asdict())

async def get_node_by_canonical_name(db: AsyncSession, canonical_name: str) -> Optional[Node]:
    """Retrieves a node by its canonical name."""
    query = text("SELECT * FROM nodes WHERE canonical_name = :canonical_name;")
    result = await db.execute(query, {"canonical_name": canonical_name})
    row = result.first()
    if row:
        return Node(**row._asdict())
    return None

async def get_nodes_by_ids(db: AsyncSession, node_ids: List[str]) -> List[Node]:
    """Retrieves nodes by a list of IDs."""
    if not node_ids: return []
    query = text("SELECT * FROM nodes WHERE id = ANY(:node_ids);")
    result = await db.execute(query, {"node_ids": node_ids})
    return [Node(**row._asdict()) for row in result.all()]

async def search_embeddings(db: AsyncSession, query_embedding: List[float], top_k: int = 5) -> List[Embedding]:
    """Performs a similarity search on embeddings."""
    query = text("""
        SELECT id, node_id, content, embedding, 1 - (embedding <=> :query_embedding) AS similarity
        FROM embeddings
        ORDER BY embedding <=> :query_embedding
        LIMIT :top_k;
    """).bindparams(query_embedding=Vector(query_embedding))
    result = await db.execute(query, {"top_k": top_k})
    # Note: The embedding field retrieved is a string representation, not a list of floats directly.
    # You might need a conversion or rely on other fields.
    # For simplicity, we'll return a partial Embedding object here, actual embedding list might need parsing.
    return [Embedding(id=row.id, node_id=row.node_id, content=row.content, embedding=[]) for row in result.all()] # Embedding list is left empty for now

async def get_graph_stats(db: AsyncSession) -> Dict[str, Any]:
    """Retrieves basic statistics about the graph."""
    node_count = await db.scalar(text("SELECT COUNT(*) FROM nodes;"))
    edge_count = await db.scalar(text("SELECT COUNT(*) FROM edges;"))
    embedding_count = await db.scalar(text("SELECT COUNT(*) FROM embeddings;"))
    raw_log_count = await db.scalar(text("SELECT COUNT(*) FROM raw_logs;"))

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "embedding_count": embedding_count,
        "raw_log_count": raw_log_count
    }
