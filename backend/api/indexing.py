# backend/api/indexing.py
from __future__ import annotations

import io
import threading
from typing import List

from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Tenant, AppUser, Document, Chunk
from .embeddings import embed_texts


# -------------------- WebSocket progress helpers --------------------

def _sanitize_group(s: str) -> str:
    """Channels requires ASCII [A-Za-z0-9_.-] and < 100 char."""
    return "".join(c if (c.isalnum() or c in "._-") else "_" for c in s)[:90]


def _progress_group(tenant_key: str, sub: str) -> str:
    return _sanitize_group(f"progress.{tenant_key or 'default'}.{sub or 'anon'}")


def _send_progress(tenant_key: str, sub: str, stage: str, message: str, extra: dict | None = None):
    """
    Helper to send progress updates to WebSocket clients via Redis/Channels.
    """
    try:
        ch = get_channel_layer()
        if not ch:
            print("⚠️ No channel layer found (Redis not configured?)")
            return

        payload = {"stage": stage, "message": message}
        if extra:
            payload.update(extra)

        group = _progress_group(tenant_key, sub)
        async_to_sync(ch.group_send)(
            group,
            {"type": "progress.event", "payload": payload},
        )
        print(f"📡 Sent progress → {group}: {stage} - {message}")

    except Exception as e:
        print(f"⚠️ Failed to send progress: {e}")


# -------------------- Extraction --------------------

def _extract_text_pdf(content: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text
        with io.BytesIO(content) as f:
            return extract_text(f) or ""
    except Exception as e:
        print(f"⚠️ PDF extract failed: {e}")
        return ""


def _extract_text_plain(content: bytes) -> str:
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ Plain extract failed: {e}")
        return ""


def _extract_text_markdown(content: bytes) -> str:
    return _extract_text_plain(content)


def extract_text_by_type(content: bytes, content_type: str, filename: str) -> str:
    ctype = (content_type or "").lower()
    name = (filename or "").lower()
    if ctype.startswith("application/pdf") or name.endswith(".pdf"):
        return _extract_text_pdf(content)
    if name.endswith(".md") or ctype.startswith("text/markdown"):
        return _extract_text_markdown(content)
    return _extract_text_plain(content)


# -------------------- Chunking --------------------

def chunk_text(text: str, size: int = 1200, overlap: int = 100) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    i, n = 0, len(text)
    while i < n:
        j = min(i + size, n)
        out.append(text[i:j])
        i = j - overlap if j - overlap > i else j
    return out


# -------------------- Main worker --------------------

def index_file(sub: str, tenant_key: str, filename: str, content: bytes, content_type: str):
    """Background worker that indexes a file and emits WebSocket progress events."""
    try:
        _send_progress(tenant_key, sub, "queued", f"Queued {filename}")

        # Resolve tenant & app user
        tenant, _ = Tenant.objects.get_or_create(
            key=tenant_key or "default",
            defaults={"name": tenant_key or "default"},
        )
        user, _ = AppUser.objects.get_or_create(
            tenant=tenant,
            sub=sub,
            defaults={"email": ""},
        )

        # Reading / extraction
        _send_progress(tenant_key, sub, "reading", f"Reading {filename}")
        text = extract_text_by_type(content, content_type, filename)
        if not text.strip():
            _send_progress(tenant_key, sub, "error", f"No text extracted from {filename}")
            return

        # Create Document
        with transaction.atomic():
            doc = Document.objects.create(
                tenant=tenant,
                owner=user,
                filename=filename,
                content_type=content_type or "application/octet-stream",
            )

        # Chunk
        _send_progress(tenant_key, sub, "chunking", f"Chunking {filename}")
        pieces = chunk_text(text)
        if not pieces:
            _send_progress(tenant_key, sub, "error", f"No chunks produced for {filename}")
            return

        # Embed
        _send_progress(tenant_key, sub, "embedding", f"Embedding {len(pieces)} chunks")
        vectors = embed_texts(pieces)

        # Sanity check embedding shape
        if not vectors or len(vectors) != len(pieces):
            _send_progress(tenant_key, sub, "error", f"Embedding mismatch {len(vectors)}/{len(pieces)}")
            return
        if any(len(v) != 1536 for v in vectors):
            _send_progress(tenant_key, sub, "error", "Embedding dimension mismatch (expected 1536)")
            return

        # Persist chunks
        rows = [
            Chunk(document=doc, text=t, section="Body", embedding=v)
            for t, v in zip(pieces, vectors)
        ]
        Chunk.objects.bulk_create(rows, batch_size=100)

        # Done!
        _send_progress(tenant_key, sub, "indexed", f"Indexed {filename}", {"doc_id": doc.id})

    except Exception as e:
        _send_progress(tenant_key, sub, "error", f"{filename}: {e.__class__.__name__}: {e}")


def index_file_async(sub: str, tenant_key: str, filename: str, content: bytes, content_type: str):
    """Spawn a thread to index file and return immediately."""
    threading.Thread(
        target=index_file,
        args=(sub, tenant_key, filename, content, content_type),
        daemon=True,
    ).start()
