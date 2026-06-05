import os
import json
from typing import List, dict
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Local imports
from vector_db.embeddings import get_embedding

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/rag_db")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """
    Initializes PostgreSQL database, ensures pgvector extension is active,
    creates documents table, and sets up GIN index for full-text search.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create documents table with a 1024-dimension vector column (BGE Large)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50) NOT NULL, -- confluence, jira, slack
                title TEXT,
                content TEXT NOT NULL,
                url TEXT,
                ticket_id VARCHAR(50),
                status VARCHAR(50),
                channel VARCHAR(100),
                sender VARCHAR(100),
                department VARCHAR(100) NOT NULL,
                clearance_level INT NOT NULL,
                embedding vector(1024),
                fts_vector tsvector
            );
        """)
        
        # Create full-text search update trigger
        cur.execute("""
            CREATE OR REPLACE FUNCTION documents_fts_trigger() RETURNS trigger AS $$
            begin
              new.fts_vector :=
                to_tsvector('english', coalesce(new.title, '')) ||
                to_tsvector('english', coalesce(new.content, ''));
              return new;
            end
            $$ LANGUAGE plpgsql;
        """)
        
        cur.execute("""
            CREATE OR REPLACE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
            ON documents FOR EACH ROW EXECUTE FUNCTION documents_fts_trigger();
        """)
        
        # Create index on embedding and tsvector for quick queries
        cur.execute("CREATE INDEX IF NOT EXISTS doc_fts_idx ON documents USING GIN(fts_vector);")
        # vector index can be IVFFlat or HNSW (HNSW is generally preferred for performance)
        cur.execute("CREATE INDEX IF NOT EXISTS doc_vector_idx ON documents USING hnsw (embedding vector_cosine_ops);")
        
        conn.commit()
        print("Database initialized successfully with pgvector and full-text indexes.")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
    finally:
        cur.close()
        conn.close()

def insert_document(doc: dict):
    """
    Inserts a single document and generates its embedding.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        emb = get_embedding(doc["content"])
        
        cur.execute("""
            INSERT INTO documents (
                source, title, content, url, ticket_id, status, channel, sender, department, clearance_level, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            doc["source"],
            doc.get("title"),
            doc["content"],
            doc.get("url"),
            doc.get("ticket_id"),
            doc.get("status"),
            doc.get("channel"),
            doc.get("sender"),
            doc.get("department"),
            doc.get("clearance_level", 1),
            emb
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def reciprocal_rank_fusion(dense_results: List[dict], sparse_results: List[dict], k: int = 60) -> List[dict]:
    """
    Combines two ranked lists of results using Reciprocal Rank Fusion.
    """
    rrf_scores = {}
    doc_map = {}
    
    # Process dense embeddings rank
    for rank, doc in enumerate(dense_results):
        doc_id = doc["id"]
        doc_map[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        
    # Process keyword search rank
    for rank, doc in enumerate(sparse_results):
        doc_id = doc["id"]
        doc_map[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        
    # Sort documents by their accumulated RRF score
    sorted_doc_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    fused_docs = []
    for doc_id, score in sorted_doc_ids:
        doc = doc_map[doc_id]
        doc["rrf_score"] = score
        fused_docs.append(doc)
        
    return fused_docs

def search_db(query: str, source: str, department: str, clearance_level: int, limit: int = 20) -> List[dict]:
    """
    Main entry point for security-filtered hybrid search.
    1. Converts query to embedding.
    2. Runs vector similarity query (pgvector).
    3. Runs standard postgres full-text text matching.
    4. Merges dense & sparse results via Reciprocal Rank Fusion.
    5. Returns unified security-filtered document results.
    """
    conn = get_connection()
    # Use RealDictCursor to return results as clean python dictionaries
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Enforce security context: Users see items from their own department
        # or globally shared channels, up to their authorization clearance level.
        # This matches the user's diagram specification:
        # "RBAC Metadata Filter injected (WHERE department = ? AND clearance_level >= ?)"
        # Note: Clearance level checks represent <= permission (lower clearance level is less restrictive, e.g. Intern=1, Admin=3).
        security_query = """
            (department = %s OR department = 'Shared')
            AND clearance_level <= %s
            AND source = %s
        """
        
        # 1. Sparse Search (BM25 Full Text Search in Postgres)
        cur.execute(f"""
            SELECT id, source, title, content, url, ticket_id, status, channel, sender, department, clearance_level,
                   ts_rank(fts_vector, plainto_tsquery('english', %s)) as rank
            FROM documents
            WHERE {security_query} AND fts_vector @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """, (query, department, clearance_level, source, query, limit))
        sparse_results = cur.fetchall()
        
        # 2. Dense Search (pgvector Cosine Distance)
        query_emb = get_embedding(query)
        cur.execute(f"""
            SELECT id, source, title, content, url, ticket_id, status, channel, sender, department, clearance_level,
                   (1 - (embedding <=> %s::vector)) as similarity
            FROM documents
            WHERE {security_query}
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s
        """, (query_emb, department, clearance_level, source, query_emb, limit))
        dense_results = cur.fetchall()
        
        # Convert RealDictCursor objects to standard dicts
        sparse_results_dict = [dict(row) for row in sparse_results]
        dense_results_dict = [dict(row) for row in dense_results]
        
        # 3. Apply Reciprocal Rank Fusion (RRF)
        fused_results = reciprocal_rank_fusion(dense_results_dict, sparse_results_dict)
        return fused_results[:limit]
        
    except Exception as e:
        print(f"Error performing hybrid search: {e}")
        return []
    finally:
        cur.close()
        conn.close()
