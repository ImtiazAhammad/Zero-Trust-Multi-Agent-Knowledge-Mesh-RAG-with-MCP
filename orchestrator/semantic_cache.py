import os
import json
import uuid
import httpx
import numpy as np
import redis.asyncio as redis
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")

async def get_embedding_async(text: str) -> List[float]:
    """
    Fetches the dense vector embedding for the given text.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json={"texts": [text]},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes cosine similarity between two vectors.
    """
    a = np.array(v1)
    b = np.array(v2)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

async def cache_lookup(query: str, threshold: float = 0.92) -> Optional[str]:
    """
    Looks up a semantically similar query in the Redis cache.
    1. Embed the query.
    2. Retrieve all keys matching 'cache:*'.
    3. Retrieve the cached vectors and compute similarity.
    4. Return the cached answer if similarity >= threshold.
    """
    # 1. Embed incoming query
    query_vector = await get_embedding_async(query)
    
    # 2. Connect to Redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        # 3. Retrieve all cache keys
        keys = await r.keys("cache:*")
        
        # 4. Compare similarities
        for key in keys:
            val_str = await r.get(key)
            if val_str:
                try:
                    data = json.loads(val_str)
                    cached_vector = data.get("embedding")
                    cached_answer = data.get("answer")
                    
                    if cached_vector and cached_answer:
                        sim = cosine_similarity(query_vector, cached_vector)
                        print(f"[Semantic Cache] Comparing with key '{key}'. Similarity: {sim:.4f}")
                        if sim >= threshold:
                            print(f"[Semantic Cache] HIT: '{query}' matches cached key '{key}' (Similarity: {sim:.4f})")
                            return cached_answer
                except Exception as e:
                    print(f"[Semantic Cache] Error parsing cache key '{key}': {e}")
    finally:
        await r.aclose()
        
    print(f"[Semantic Cache] MISS: '{query}'")
    return None

async def cache_store(query: str, answer: str):
    """
    Stores the query embedding and its answer in the Redis cache with a 3600-second TTL.
    """
    # 1. Embed query
    query_vector = await get_embedding_async(query)
    
    # 2. Store in Redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        cache_id = str(uuid.uuid4())
        key = f"cache:{cache_id}"
        val = {
            "embedding": query_vector,
            "answer": answer
        }
        await r.setex(key, 3600, json.dumps(val))
        print(f"[Semantic Cache] Stored answer for query: '{query}' at key '{key}'")
    finally:
        await r.aclose()
