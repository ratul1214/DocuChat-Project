import numpy as np
from typing import List, Tuple
from django.conf import settings
from .models import Chunk


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def search(owner_sub: str, query_embedding: List[float], top_k: int) -> List[Tuple[Chunk, float]]:
    q = np.array(query_embedding, dtype=float)
    results = []
    for ch in Chunk.objects.filter(owner_sub=owner_sub).select_related('document'):
        e = np.array(ch.embedding, dtype=float)
        sim = _cosine(q, e)
        results.append((ch, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
