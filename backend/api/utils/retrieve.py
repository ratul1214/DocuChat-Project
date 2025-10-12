import numpy as np
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
from django.db.models import F
from .models import Chunk
from openai import OpenAI

client = OpenAI()

def embed_query(text: str):
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(resp.data[0].embedding, dtype=np.float32)

def hybrid_search(query_text: str, tenant, top_k=5):
    q_emb = embed_query(query_text)

    # Step 1: FTS candidates
    search_query = SearchQuery(query_text)
    fts_candidates = (
        Chunk.objects.filter(document__tenant=tenant)
        .annotate(rank=SearchRank(F("tsv"), search_query))
        .filter(rank__gt=0.001)
        .order_by("-rank")[:top_k * 4]
    )

    # Step 2: Vector candidates
    sql = """
    SELECT id, (1 - (embedding <=> %s)) AS sim
    FROM api_chunk
    WHERE document_id IN (
        SELECT id FROM api_document WHERE tenant_id = %s
    )
    ORDER BY embedding <=> %s
    LIMIT %s
    """
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute(sql, [list(q_emb), tenant.id, list(q_emb), top_k * 4])
        vector_results = {r[0]: float(r[1]) for r in cur.fetchall()}

    # Step 3: Combine & re-rank
    combined = {}
    for c in fts_candidates:
        combined[c.id] = {"chunk": c, "score": 0.4 * c.rank}
    for cid, vsim in vector_results.items():
        if cid in combined:
            combined[cid]["score"] += 0.6 * vsim
        else:
            try:
                c = Chunk.objects.get(id=cid)
                combined[cid] = {"chunk": c, "score": 0.6 * vsim}
            except Chunk.DoesNotExist:
                continue

    # Step 4: sort by combined score
    sorted_results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:top_k]

    # Format citations
    hits = [
        {
            "text": res["chunk"].text[:200],
            "section": res["chunk"].section,
            "page_range": [res["chunk"].page_start, res["chunk"].page_end],
            "score": round(res["score"], 4),
            "doc": res["chunk"].document.filename,
        }
        for res in sorted_results
    ]
    return hits
