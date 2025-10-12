import os, math, time, hashlib, random
from typing import List

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
MAX_TOKENS_PER_REQ = int(os.getenv("EMBED_TOKENS_PER_REQ", "250000"))

def _approx_tokens(s: str) -> int:
    return max(1, math.ceil(len(s) / 4))

def _stub_vec(seed: str, dim: int = 1536) -> List[float]:
    # deterministic per input string
    rnd = random.Random(int(hashlib.sha1(seed.encode()).hexdigest(), 16) % (10**8))
    return [rnd.uniform(-0.01, 0.01) for _ in range(dim)]

class Embedder:
    def __init__(self, api_key=None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)

    def _embed_batch(self, batch: List[str]) -> List[List[float]]:
        if not self.client:  # stub path
            return [_stub_vec(t) for t in batch]
        resp = self.client.embeddings.create(model=self.model, input=batch)
        return [d.embedding for d in resp.data]

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        cur: List[str] = []
        cur_tokens = 0

        def flush():
            nonlocal out, cur, cur_tokens
            if not cur:
                return
            if not self.client:
                out.extend([_stub_vec(t) for t in cur])
                cur.clear(); cur_tokens = 0
                return
            # OpenAI path with bisection on token errors
            from openai import BadRequestError
            lo, hi = 0, len(cur)
            while lo < hi:
                try:
                    out.extend(self._embed_batch(cur[lo:hi]))
                    lo = hi
                except BadRequestError as e:
                    msg = str(e).lower()
                    if "max_tokens_per_request" in msg or "max tokens" in msg:
                        if hi - lo == 1:
                            # single too large, fall back to stub for that one
                            out.extend([_stub_vec(cur[lo])])
                            lo = hi
                        else:
                            hi = lo + (hi - lo)//2
                            time.sleep(0.1)
                    else:
                        raise
            cur.clear(); cur_tokens = 0

        for t in texts:
            tks = _approx_tokens(t)
            if cur and cur_tokens + tks > MAX_TOKENS_PER_REQ:
                flush()
            cur.append(t); cur_tokens += tks
        flush()
        return out

EMBEDDER = Embedder()

def embed_texts(texts: List[str]) -> List[List[float]]:
    return EMBEDDER.embed(texts)
