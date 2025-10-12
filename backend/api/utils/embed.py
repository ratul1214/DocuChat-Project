# backend/api/embeddings.py
import os
from openai import OpenAI

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

class Embedder:
    def __init__(self, api_key=None, model: str = DEFAULT_MODEL):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Batch embed
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

EMBEDDER = Embedder()

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convenience function used by indexing.py"""
    return EMBEDDER.embed(texts)
