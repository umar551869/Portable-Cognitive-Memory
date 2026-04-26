
-- Enable the pgvector extension
-- You might need to enable this directly in Supabase UI under Database -> Extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- nodes table
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases JSONB DEFAULT '[]'::jsonb,
    weight INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_nodes_type ON nodes (type);
CREATE INDEX idx_nodes_canonical_name ON nodes (canonical_name);

-- edges table
CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    relation TEXT NOT NULL,
    weight INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_edges_source ON edges (source);
CREATE INDEX idx_edges_target ON edges (target);
CREATE INDEX idx_edges_relation ON edges (relation);

-- embeddings table (pgvector)
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    node_id TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- Assuming OpenAI's text-embedding-ada-002 dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_embeddings_node_id ON embeddings (node_id);
CREATE INDEX ON embeddings USING ivfflat (embedding vector_l2_ops);

-- raw_logs table
CREATE TABLE raw_logs (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_logs_source_path ON raw_logs (source_path);
