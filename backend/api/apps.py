# backend/api/apps.py
from django.apps import AppConfig
from django.db.backends.signals import connection_created

def _register_pgvector(django_connection):
    """
    Register pgvector adapters on the underlying psycopg3 connection.
    Needed only if you run *raw SQL* with vectors. The ORM + VectorField
    works without this.
    """
    try:
        # Django connection wrapper -> raw psycopg connection
        raw = getattr(django_connection, "connection", None)
        if raw is None:
            return  # not yet established

        # Prevent double registration per connection
        if getattr(raw, "_pgvector_registered", False):
            return

        from pgvector.psycopg import register_vector  # psycopg3 adapter
        register_vector(raw)
        setattr(raw, "_pgvector_registered", True)
    except Exception as e:
        # Don't break startup on registration hiccups
        print("pgvector registration warning:", e)

class ApiConfig(AppConfig):
    name = "api"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # weak=False so our lambda isn't GC'd
        connection_created.connect(
            lambda sender, connection, **kw: _register_pgvector(connection),
            weak=False,
        )
