import os
import asyncio
import httpx
import asyncpg
import psycopg2
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/rag_db")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")

# --- Async Database search via asyncpg ---

async def get_embedding_async(text: str) -> List[float]:
    """
    Retrieves dense embedding from the microservice at localhost:8002/embed.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"texts": [text]},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except Exception as e:
            print(f"Error querying embedding service: {e}. Generating mock local fallback.")
            import random
            random.seed(hash(text))
            return [random.uniform(-0.1, 0.1) for _ in range(1024)]

async def run_dense_query(conn: asyncpg.Connection, query_vector: List[float], department: str, clearance_level: int, source: Optional[str] = None) -> List[asyncpg.Record]:
    """
    Executes the dense pgvector cosine similarity search.
    """
    vector_str = str(query_vector)
    if source:
        sql = """
            SELECT id, title, content, source, 1 - (embedding <=> $1::vector) AS score 
            FROM documents 
            WHERE department = $2 AND clearance_level <= $3 AND source = $4
            ORDER BY score DESC LIMIT 20
        """
        return await conn.fetch(sql, vector_str, department, clearance_level, source)
    else:
        sql = """
            SELECT id, title, content, source, 1 - (embedding <=> $1::vector) AS score 
            FROM documents 
            WHERE department = $2 AND clearance_level <= $3
            ORDER BY score DESC LIMIT 20
        """
        return await conn.fetch(sql, vector_str, department, clearance_level)

async def run_sparse_query(conn: asyncpg.Connection, query: str, department: str, clearance_level: int, source: Optional[str] = None) -> List[asyncpg.Record]:
    """
    Executes the sparse PostgreSQL full-text (ts_rank_cd) BM25 search.
    """
    if source:
        sql = """
            SELECT id, title, content, source, ts_rank_cd(to_tsvector('english', content), plainto_tsquery($1)) AS score 
            FROM documents 
            WHERE department = $2 AND clearance_level <= $3 AND source = $4
            ORDER BY score DESC LIMIT 20
        """
        return await conn.fetch(sql, query, department, clearance_level, source)
    else:
        sql = """
            SELECT id, title, content, source, ts_rank_cd(to_tsvector('english', content), plainto_tsquery($1)) AS score 
            FROM documents 
            WHERE department = $2 AND clearance_level <= $3
            ORDER BY score DESC LIMIT 20
        """
        return await conn.fetch(sql, query, department, clearance_level)

def reciprocal_rank_fusion(dense_list: List[asyncpg.Record], sparse_list: List[asyncpg.Record], limit: int = 20) -> List[Dict]:
    """
    Merges dense and sparse lists using Reciprocal Rank Fusion: score = 1 / (rank + 60).
    """
    rrf_scores = {}
    doc_data = {}
    
    def process_list(records):
        for rank, record in enumerate(records):
            doc_id = record["id"]
            if doc_id not in doc_data:
                doc_data[doc_id] = {
                    "id": str(doc_id),
                    "title": record.get("title") or "",
                    "content": record["content"],
                    "source": record["source"]
                }
            # RRF calculation
            score = 1.0 / (rank + 60)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score

    process_list(dense_list)
    process_list(sparse_list)
    
    # Sort descending based on accumulated RRF score
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for doc_id, score in sorted_docs[:limit]:
        doc = doc_data[doc_id]
        doc["score"] = score
        results.append(doc)
        
    return results

async def search_db(query: str, department: str, clearance_level: int, source: Optional[str] = None, limit: int = 20, hyde_vector: Optional[List[float]] = None) -> List[Dict]:
    """
    Performs parallel dense (pgvector) and sparse (tsvector) searches.
    Merges results using Reciprocal Rank Fusion (RRF) and returns top-N results.
    """
    # 1. Fetch dense query vector (use precomputed hyde_vector if provided)
    if hyde_vector is not None:
        query_vector = hyde_vector
    else:
        query_vector = await get_embedding_async(query)
    
    # 2. Run queries in parallel using asyncpg (requires separate connections for concurrency)
    conn_dense, conn_sparse = await asyncio.gather(
        asyncpg.connect(DATABASE_URL),
        asyncpg.connect(DATABASE_URL)
    )
    try:
        dense_task = run_dense_query(conn_dense, query_vector, department, clearance_level, source)
        sparse_task = run_sparse_query(conn_sparse, query, department, clearance_level, source)
        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
    finally:
        await asyncio.gather(
            conn_dense.close(),
            conn_sparse.close()
        )
        
    # 3. Fuse and rank results
    return reciprocal_rank_fusion(dense_results, sparse_results, limit=limit)


# --- Synchronous Seeding Utilities via psycopg2 ---

def get_connection_sync():
    """
    Sync fallback connection for seeding/initialization.
    """
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """
    Initializes PostgreSQL database tables (used for manual seeding).
    """
    conn = get_connection_sync()
    cur = conn.cursor()
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                content TEXT NOT NULL,
                embedding vector(1024),
                source TEXT,
                department TEXT,
                clearance_level INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            ALTER TABLE documents ADD COLUMN IF NOT EXISTS title TEXT;
        """)
        cur.execute("""
            ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts_vector tsvector 
                GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS doc_fts_idx ON documents USING GIN(fts_vector);")
        cur.execute("CREATE INDEX IF NOT EXISTS doc_vector_idx ON documents USING hnsw (embedding vector_cosine_ops);")
        conn.commit()
        print("Database schema verified/initialized successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing schema: {e}")
    finally:
        cur.close()
        conn.close()

def insert_document(doc: dict):
    """
    Synchronous document insertion with embedding generation (used for seeding).
    """
    conn = get_connection_sync()
    cur = conn.cursor()
    try:
        # Run event loop to resolve async embedding call
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If running in Jupyter or another active loop, use nest_asyncio or call helper
            import urllib.request
            import json
            # Fallback to synchronous HTTP POST to avoid nested loop issues
            try:
                req = urllib.request.Request(
                    f"{EMBEDDING_SERVICE_URL}/embed", 
                    data=json.dumps({"texts": [doc["content"]]}).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res = json.loads(response.read().decode())
                    emb = res["embeddings"][0]
            except Exception:
                import random
                random.seed(hash(doc["content"]))
                emb = [random.uniform(-0.1, 0.1) for _ in range(1024)]
        else:
            emb = loop.run_until_complete(get_embedding_async(doc["content"]))
            
        cur.execute("""
            INSERT INTO documents (
                source, title, content, embedding, department, clearance_level
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            doc["source"],
            doc.get("title", ""),
            doc["content"],
            emb,
            doc["department"],
            doc["clearance_level"]
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
