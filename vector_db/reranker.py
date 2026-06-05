import os
from typing import List, dict
from dotenv import load_dotenv

load_dotenv()

RERANKER_MODEL = os.getenv("RERANKER_MODEL_NAME", "ms-marco-MiniLM-L-6-v2")

# Lazy loading of FlashRank cross-encoder
_ranker = None

def get_ranker():
    global _ranker
    if _ranker is None:
        try:
            from flashrank import Ranker
            print(f"Loading FlashRank reranker model: {RERANKER_MODEL}...")
            # Initialize with default/configured model
            _ranker = Ranker(model_name=RERANKER_MODEL)
        except Exception as e:
            print(f"Failed to load FlashRank reranker: {e}")
            print("Falling back to RRF score-based sorting.")
            _ranker = "fallback"
    return _ranker

def rerank_documents(query: str, documents: List[dict], top_n: int = 5) -> List[dict]:
    """
    Reranks document chunks using FlashRank cross-encoder.
    Filters the initial set of candidate documents down to top_n results.
    """
    if not documents:
        return []
        
    ranker = get_ranker()
    if ranker == "fallback":
        # Fallback: Sort by existing similarity or rrf_score (descending)
        # If rrf_score doesn't exist, fallback to index order
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("rrf_score", x.get("similarity", 0.0)),
            reverse=True
        )
        return sorted_docs[:top_n]
        
    try:
        from flashrank import RerankRequest
        
        # Prepare list of dicts for FlashRank (requires 'id' and 'text')
        passages = []
        for i, doc in enumerate(documents):
            passages.append({
                "id": doc.get("id", i),
                "text": doc.get("content", ""),
                "meta": doc # Store the full document dictionary in metadata
            })
            
        rerank_request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerank_request)
        
        # Extract the original doc dicts, ordered by their new cross-encoder ranking
        reranked_docs = []
        for res in results[:top_n]:
            doc = res["meta"]
            doc["rerank_score"] = res.get("score")
            reranked_docs.append(doc)
            
        return reranked_docs
    except Exception as e:
        print(f"Reranking error: {e}")
        # Return fallback slice on exception
        return documents[:top_n]
