import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

app = FastAPI(
    title="BGE Embedding Microservice",
    description="Dedicated microservice exposing BAAI/bge-large-en-v1.5 text embeddings.",
    version="1.0.0"
)

# Load sentence-transformers model (downloads on startup if not cached)
MODEL_NAME = "BAAI/bge-large-en-v1.5"
print(f"Initializing SentenceTransformer with model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

@app.get("/health")
def health():
    return {"status": "healthy", "model": MODEL_NAME}

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """
    Generates BGE large en v1.5 dense vector embeddings.
    Accepts a list of texts and returns their corresponding 1024-dimensional vectors.
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="Text list cannot be empty.")
    
    try:
        # Encode inputs (automatically normalizes outputs to unit vectors)
        embeddings = model.encode(request.texts, normalize_embeddings=True)
        return EmbedResponse(embeddings=embeddings.tolist())
    except Exception as e:
        print(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")
