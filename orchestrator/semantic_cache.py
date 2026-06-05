import os
import json
import numpy as np
from typing import Optional, dict, List
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

# We can import embedding generator inside semantic_cache to generate embeddings
# from vector_db.embeddings import get_embedding

class SemanticCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None
        self.threshold = 0.90 # Cosine similarity threshold for cache hit

    async def connect(self):
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            print("Connected to Redis semantic cache.")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get(self, query: str, user_context: dict) -> Optional[dict]:
        """
        Check semantic cache in Redis.
        Filters cache entries based on user's security level (department and clearance level).
        """
        if not self.redis:
            return None
            
        try:
            # Note: For simple setup, we check keys under the user's department and clearance level
            # to prevent information leakage across access boundaries.
            dept = user_context["department"]
            clearance = user_context["clearance_level"]
            
            # Retrieve all queries for this department and clearance partition
            pattern = f"cache:{dept}:{clearance}:*"
            keys = await self.redis.keys(pattern)
            if not keys:
                return None
                
            # Compute embedding for target query
            from vector_db.embeddings import get_embedding
            target_embedding = np.array(get_embedding(query))
            
            # Simple KNN search over keys (for larger scale, Redis FT.SEARCH vector index would be used)
            best_match_key = None
            best_score = -1.0
            
            for key in keys:
                cached_data = await self.redis.get(key)
                if not cached_data:
                    continue
                data = json.loads(cached_data)
                cached_emb = np.array(data["embedding"])
                
                # Compute Cosine Similarity
                norm_a = np.linalg.norm(target_embedding)
                norm_b = np.linalg.norm(cached_emb)
                if norm_a == 0 or norm_b == 0:
                    similarity = 0
                else:
                    similarity = np.dot(target_embedding, cached_emb) / (norm_a * norm_b)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match_key = key
            
            if best_score >= self.threshold and best_match_key:
                cached_data = await self.redis.get(best_match_key)
                data = json.loads(cached_data)
                print(f"Semantic Cache Hit! Similarity: {best_score:.4f}")
                return {
                    "answer": data["answer"],
                    "source_documents": data["source_documents"]
                }
        except Exception as e:
            print(f"Error checking semantic cache: {e}")
            
        return None

    async def set(self, query: str, user_context: dict, answer: str, source_documents: List[dict]):
        """
        Save query, its embedding, answer, and source metadata into Redis.
        Partitioned by department and clearance level to safeguard security.
        """
        if not self.redis:
            return
            
        try:
            from vector_db.embeddings import get_embedding
            query_embedding = get_embedding(query)
            
            dept = user_context["department"]
            clearance = user_context["clearance_level"]
            
            # Unique cache key for the query partition
            cache_id = hash(query)
            key = f"cache:{dept}:{clearance}:{cache_id}"
            
            payload = {
                "query": query,
                "embedding": query_embedding,
                "answer": answer,
                "source_documents": source_documents,
                "created_at": str(np.datetime64('now'))
            }
            
            # Store in Redis with 1 hour TTL
            await self.redis.set(key, json.dumps(payload), ex=3600)
            print(f"Stored query in semantic cache: {key}")
        except Exception as e:
            print(f"Error saving to semantic cache: {e}")
