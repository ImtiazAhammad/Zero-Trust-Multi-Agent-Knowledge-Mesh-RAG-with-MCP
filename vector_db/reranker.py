import os
from typing import List, Dict
from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")

_model = None

def get_reranker_model():
    """
    Lazily initializes and returns the CrossEncoder reranker model.
    """
    global _model
    if _model is None:
        print(f"Loading CrossEncoder reranker model: {RERANKER_MODEL_NAME}...")
        _model = CrossEncoder(RERANKER_MODEL_NAME)
    return _model

def rerank(query: str, documents: List[Dict]) -> List[Dict]:
    """
    Reranks documents using a CrossEncoder based on semantic relevance to the query.
    Accepts the top hybrid search results, scores them in a single batch, and
    returns the top-5 documents sorted by cross-encoder score descending.
    """
    if not documents:
        return []

    model = get_reranker_model()

    # Score all (query, document content) pairs in a single batch
    pairs = [[query, doc["content"]] for doc in documents]
    scores = model.predict(pairs)

    # Attach scores to each document
    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    # Sort descending by cross-encoder score
    sorted_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
    
    # Return top 5 documents
    return sorted_docs[:5]
