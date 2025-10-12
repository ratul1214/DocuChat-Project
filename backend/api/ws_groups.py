# backend/api/ws_groups.py
ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

def sanitize(s: str) -> str:
    return "".join(c if c in ALLOWED else "_" for c in (s or ""))[:90]

def progress_group(sub: str) -> str:
    return f"progress.{sanitize(sub or 'anon')}"
