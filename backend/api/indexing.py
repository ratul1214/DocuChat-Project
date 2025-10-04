import io
import threading
from typing import List
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Document, Chunk
from .embeddings import Embedder

EMBEDDER = Embedder()


def _send_progress(sub: str, payload: dict):
    group = f"progress.{sub}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(group, {"type": "progress.message", "payload": payload})


def _extract_text(filename: str, content: bytes, content_type: str) -> str:
    if content_type in ('text/plain',) or filename.lower().endswith('.txt'):
        return content.decode('utf-8', errors='ignore')
    if content_type in ('text/markdown',) or filename.lower().endswith('.md'):
        return content.decode('utf-8', errors='ignore')
    if content_type in ('application/pdf',) or filename.lower().endswith('.pdf'):
        from pdfminer.high_level import extract_text
        with io.BytesIO(content) as f:
            return extract_text(f)
    # Fallback: treat as text
    return content.decode('utf-8', errors='ignore')


def _chunk_text(text: str, max_tokens: int, overlap: int) -> List[str]:
    # Token-agnostic MVP: split by ~max_tokens words
    words = text.split()
    chunks = []
    i = 0
    step = max_tokens - overlap
    if step <= 0:
        step = max_tokens
    while i < len(words):
        chunk_words = words[i:i + max_tokens]
        chunks.append(' '.join(chunk_words))
        i += step
    return chunks


def index_file(owner_sub: str, filename: str, content: bytes, content_type: str):
    _send_progress(owner_sub, {"stage": "received", "filename": filename})
    text = _extract_text(filename, content, content_type)
    doc = Document.objects.create(owner_sub=owner_sub, filename=filename, content_type=content_type, text=text)

    _send_progress(owner_sub, {"stage": "chunking", "filename": filename})
    chunks = _chunk_text(text, settings.MAX_CHUNK_TOKENS, settings.CHUNK_OVERLAP_TOKENS)

    _send_progress(owner_sub, {"stage": "embedding", "filename": filename, "chunks": len(chunks)})
    vectors = EMBEDDER.embed(chunks)

    objs = [Chunk(document=doc, owner_sub=owner_sub, idx=i, text=ch, embedding=vectors[i]) for i, ch in enumerate(chunks)]
    Chunk.objects.bulk_create(objs, batch_size=100)

    _send_progress(owner_sub, {"stage": "done", "filename": filename, "chunks": len(chunks)})


def index_file_async(owner_sub: str, filename: str, content: bytes, content_type: str):
    # Lightweight background thread for MVP (no Celery in Step 1)
    threading.Thread(target=index_file, args=(owner_sub, filename, content, content_type), daemon=True).start()
