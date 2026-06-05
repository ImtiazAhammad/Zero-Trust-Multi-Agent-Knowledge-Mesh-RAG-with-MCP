# Use a lightweight python base image
FROM python:3.10-slim

WORKDIR /app

# Install dependencies, prioritizing CPU-only torch to keep image size small
# (preserves VRAM for the main vLLM model service)
RUN pip install --no-cache-dir torch>=2.4.0 --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir sentence-transformers fastapi uvicorn pydantic

# Pre-download the model so it does not fetch it at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

# Copy application code
COPY main.py .

# Expose microservice port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
