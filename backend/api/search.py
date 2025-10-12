# backend/api/search.py
from typing import List, Tuple
from django.db.models.expressions import RawSQL
from .models import Chunk, Tenant
from .embeddings import embed_texts

W_VEC = 0.5
W_TS = 0.5

def _hybrid_search(query: str, tenant: Tenant, top_k: int = 5) -> List[Tuple[Chunk, float, float, float]]:
    qvec = embed_texts([query])[0]  # list[float]

    sim_vec_sql = RawSQL("1 - (embedding <=> %s::vector)", (qvec,))
    rank_ts_sql = RawSQL("ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s))", (query,))
    score_sql = RawSQL(
        "%s * (1 - (embedding <=> %s::vector)) + %s * ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s))",
        (W_VEC, qvec, W_TS, query),
    )

    qs = (
        Chunk.objects
        .filter(document__tenant=tenant)
        .annotate(sim_vec=sim_vec_sql, rank_ts=rank_ts_sql, score=score_sql)
        .order_by("-score")
    )

    results = []
    for c in qs[:max(1, top_k)]:
        results.append((
            c,
            float(c.score or 0.0),
            float(c.sim_vec or 0.0),
            float(c.rank_ts or 0.0),
        ))
    return results

import hashlib
from django.core.cache import cache
# ... your existing imports ...

def _ck_hybrid(query: str, tenant_id: int, top_k: int) -> str:
    h = hashlib.sha1(f"{tenant_id}:{top_k}:{query}".encode()).hexdigest()
    return f"hybrid:{h}"

def hybrid_search(query: str, tenant, top_k: int = 5):
    ck = _ck_hybrid(query, tenant.id, top_k)
    cached = cache.get(ck)
    if cached is not None:
        return cached  # [(chunk, score, bm25, dense), ...]

    # --- your existing retrieval logic ---
    results = _hybrid_search(query, tenant, top_k)

    cache.set(ck, results, timeout=60)  # 60s cache
    return results