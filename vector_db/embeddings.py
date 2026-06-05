import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")

def get_embedding(text: str) -> List[float]:
    """
    Generates a dense vector embedding for the given text.
    Queries the BGE embedding microservice, falling back to deterministic mock embeddings on failure.
    """
    try:
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed", 
            json={"texts": [text]}, 
            timeout=10
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]
    except Exception as e:
        print(f"Embedding service call failed ({e}). Falling back to mock local vectors.")
        # Return a deterministic mock vector of size 1024 based on hash of text
        import random
        random.seed(hash(text))
        return [random.uniform(-0.1, 0.1) for _ in range(1024)]

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates dense embeddings for a list of texts by calling the BGE microservice.
    """
    if not texts:
        return []
    try:
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed", 
            json={"texts": texts}, 
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    except Exception as e:
        print(f"Embedding service batch call failed ({e}). Falling back to mock local vectors.")
        return [get_embedding(t) for t in texts]
