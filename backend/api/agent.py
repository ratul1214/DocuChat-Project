# backend/api/agent.py
import json, threading, textwrap
from django.conf import settings
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Report, AppUser, Tenant
from .search import hybrid_search
from .embeddings import EMBEDDER
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)
LLM_MODEL = getattr(settings, "LLM_MODEL", "gpt-4o-mini")

def _send_progress(group: str, kind: str, data: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {"type": "progress.event", "text": json.dumps({"kind": kind, "data": data})},
    )

def _md_h1(t): return f"# {t}\n\n"

def run_agent(report_id: int, tenant: Tenant, user: AppUser, topic: str, top_k: int = 6):
    group = f"progress:{user.sub or user.id}"
    report = Report.objects.get(id=report_id)
    try:
        report.status = "running"
        report.save(update_fields=["status"])

        # 1) Plan
        _send_progress(group, "plan", {"msg": "Planning outline"})
        plan_prompt = f"Create a concise outline for a short report answering: {topic}"
        plan = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system","content":"You write structured, concise outlines."},
                      {"role": "user","content": plan_prompt}],
            temperature=0.2,
        ).choices[0].message.content

        # 2) Search (hybrid)
        _send_progress(group, "search", {"msg": "Retrieving supporting chunks", "top_k": top_k})
        hits = hybrid_search(topic, tenant, top_k=top_k)  # [(chunk, score), ...]
        contexts = []
        for i,(ch,score) in enumerate(hits, start=1):
            contexts.append(f"[{i}] {ch.section or ''} p.{ch.page_start}-{ch.page_end}\n{ch.text}\n")

        # 3) Synthesize
        _send_progress(group, "synthesize", {"msg": "Synthesizing with citations"})
        system = "Answer with grounded citations like [1], [2]. Be concise but complete. Return Markdown."
        user_msg = textwrap.dedent(f"""
        Question: {topic}

        Outline:
        {plan}

        Context (top-{top_k} chunks):
        {chr(10).join(contexts)}
        """)
        md = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user_msg}],
            temperature=0.2,
        ).choices[0].message.content

        # 4) Save
        _send_progress(group, "write", {"msg": "Writing report"})
        title = f"Agent Report — {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        report.title = title
        report.content = _md_h1(title) + (md or "")
        report.status = "done"
        report.save(update_fields=["title","content","status"])

        _send_progress(group, "done", {"report_id": report.id, "title": report.title})
    except Exception as e:
        report.status = "error"
        report.content = f"# Agent failed\n\n```\n{e}\n```"
        report.save(update_fields=["status","content"])
        _send_progress(group, "error", {"error": str(e)})

def run_agent_async(report_id: int, tenant: Tenant, user: AppUser, topic: str, top_k: int = 6):
    t = threading.Thread(target=run_agent, args=(report_id, tenant, user, topic, top_k), daemon=True)
    t.start()
