import os
import numpy as np
from typing import List

class Embedder:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.mode = 'mock' if not self.api_key else 'openai'

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.mode == 'mock':
            # Deterministic pseudo-embedding: hash → vector (MVP/testing)
            return [self._mock_embedding(t) for t in texts]
        else:
            # OpenAI-compatible embeddings API
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.embeddings.create(model=self.model, input=texts)
            return [d.embedding for d in resp.data]

    def _mock_embedding(self, text: str, dim: int = 256) -> List[float]:
        import hashlib, random
        h = hashlib.sha256(text.encode('utf-8')).digest()
        rng = random.Random(h)
        return [rng.uniform(-1, 1) for _ in range(dim)]
