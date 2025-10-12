# backend/api/views_metrics.py
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from .models import Tenant, AppUser, Document, Chunk, Report

STARTED_AT = timezone.now()

def _prom_line(name: str, value, labels: dict | None = None):
    if labels:
        lbl = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{name}{{{lbl}}} {value}\n"
    return f"{name} {value}\n"

def _prom_help_type(name: str, help_: str, typ: str):
    return f"# HELP {name} {help_}\n# TYPE {name} {typ}\n"

class MetricsView:
    # simple callable view (no DRF, no extra deps)
    def __call__(self, request):
        # counters
        tenants = Tenant.objects.count()
        users   = AppUser.objects.count()
        docs    = Document.objects.count()
        chunks  = Chunk.objects.count()
        reports = Report.objects.count()

        # optional per-tenant doc count
        per_tenant = (
            Document.objects.values("tenant__key").annotate(n=Count("id")).order_by("tenant__key")
        )

        # build Prometheus text exposition
        lines = []
        lines.append(_prom_help_type("app_up", "Application up flag", "gauge"))
        lines.append(_prom_line("app_up", 1))

        lines.append(_prom_help_type("app_info", "Build/info label metric", "gauge"))
        lines.append(_prom_line("app_info", 1, {"service": "docuchat", "stage": "dev"}))

        lines.append(_prom_help_type("docuchat_tenants_total", "Total tenants", "gauge"))
        lines.append(_prom_line("docuchat_tenants_total", tenants))

        lines.append(_prom_help_type("docuchat_users_total", "Total users", "gauge"))
        lines.append(_prom_line("docuchat_users_total", users))

        lines.append(_prom_help_type("docuchat_documents_total", "Total documents", "gauge"))
        lines.append(_prom_line("docuchat_documents_total", docs))

        lines.append(_prom_help_type("docuchat_chunks_total", "Total chunks", "gauge"))
        lines.append(_prom_line("docuchat_chunks_total", chunks))

        lines.append(_prom_help_type("docuchat_reports_total", "Total reports", "gauge"))
        lines.append(_prom_line("docuchat_reports_total", reports))

        lines.append(_prom_help_type("docuchat_documents_per_tenant", "Documents per tenant", "gauge"))
        for row in per_tenant:
            lines.append(_prom_line("docuchat_documents_per_tenant", row["n"], {"tenant": row["tenant__key"]}))

        body = "".join(lines)
        return HttpResponse(body, content_type="text/plain; version=0.0.4; charset=utf-8")
