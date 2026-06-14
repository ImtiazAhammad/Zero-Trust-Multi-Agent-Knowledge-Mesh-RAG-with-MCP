import os
import httpx
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:8001/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "mock-key")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")

# Initialize Async OpenAI Client for vLLM
openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)

async def generate_hyde_embedding(query: str) -> List[float]:
    """
    Implements Hypothetical Document Embeddings (HyDE):
    1. Prompt vLLM to write a hypothetical knowledge base response for the query.
    2. Retrieve dense BGE embedding for the hypothetical answer.
    3. Return the dense vector.
    """
    prompt = f"Write a short, factual paragraph (3-4 sentences) that would perfectly answer this question if it appeared in a corporate knowledge base: {query}"
    
    # 1. Ask vLLM to generate the hypothetical document
    completion = await openai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a corporate knowledge base assistant. Write a factual, concise response."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    hypothetical_answer = completion.choices[0].message.content.strip()
    
    # 2. Get dense embedding of the hypothetical answer from the embedding microservice
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json={"texts": [hypothetical_answer]},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]
