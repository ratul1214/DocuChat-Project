import os, time
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache

START_TIME = time.time()

class MetricsView(View):
    """
    Minimal Prometheus-style /metrics endpoint for liveness and latency metrics.
    """
    def get(self, request):
        uptime = time.time() - START_TIME
        try:
            with connection.cursor() as c:
                c.execute("SELECT 1;")
                db_ok = True
        except Exception:
            db_ok = False

        metrics = {
            "uptime_sec": round(uptime, 1),
            "db_ok": db_ok,

            "cache_keys": len(cache.keys("*")) if hasattr(cache, "keys") else "n/a",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return JsonResponse(metrics)
