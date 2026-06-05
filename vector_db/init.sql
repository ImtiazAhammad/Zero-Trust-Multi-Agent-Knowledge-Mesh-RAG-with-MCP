-- Enable pgvector and UUID extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table with UUID identifiers and clearance claims
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding vector(1024),
    source TEXT,
    department TEXT,
    clearance_level INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Setup full-text search column that automatically parses content
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts_vector tsvector 
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- Create GIN index for fast BM25 full-text queries
CREATE INDEX IF NOT EXISTS doc_fts_idx ON documents USING GIN(fts_vector);

-- Create HNSW index for high performance vector cosine distance searches
CREATE INDEX IF NOT EXISTS doc_vector_idx ON documents USING hnsw (embedding vector_cosine_ops);
