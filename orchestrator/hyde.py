import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup OpenAI client which can point to local inference engines (vLLM, Ollama) or OpenAI APIs
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "mock-key"),
        base_url=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
    )

def expand_query(query: str, num_candidates: int = 1) -> List[str]:
    """
    Generates hypothetical document answers to expand the initial query (HyDE).
    This guides the semantic vector search towards matching relevant documents.
    """
    if not client:
        # Fallback if OpenAI client is not configured
        return [query]
        
    model_name = os.getenv("MODEL_NAME", "qwen2.5-14b")
    prompt = (
        f"Please write a hypothetical answer or passage that directly answers this query: '{query}'. "
        f"Do not write introductions or meta-commentary, write only the passage itself."
    )
    
    candidates = []
    try:
        for _ in range(num_candidates):
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful technical writing assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7,
            )
            candidate = response.choices[0].message.content.strip()
            if candidate:
                candidates.append(candidate)
    except Exception as e:
        print(f"HyDE expansion failed (falling back to original query): {e}")
        return [query]
        
    return candidates if candidates else [query]
