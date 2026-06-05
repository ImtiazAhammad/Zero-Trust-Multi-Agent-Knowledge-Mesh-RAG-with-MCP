import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")

# Initialize embedding model lazily
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {MODEL_NAME}...")
            _model = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            print(f"Failed to load sentence-transformers model '{MODEL_NAME}': {e}")
            print("Falling back to mock embeddings (1024-dimensional dummy vectors).")
            _model = "mock"
    return _model

def get_embedding(text: str) -> List[float]:
    """
    Generates a dense vector embedding for the given text.
    For BAAI/bge-large-en-v1.5, the dimension is 1024.
    """
    model = get_embedding_model()
    if model == "mock":
        # Return a deterministic mock vector of size 1024 based on hash of text
        import random
        # Seed generator with hash of text for consistent embeddings of same string
        h = hash(text)
        random.seed(h)
        mock_vec = [random.uniform(-0.1, 0.1) for _ in range(1024)]
        return mock_vec
    
    # Generate actual embedding
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates dense embeddings for a list of texts.
    """
    model = get_embedding_model()
    if model == "mock":
        return [get_embedding(t) for t in texts]
        
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
