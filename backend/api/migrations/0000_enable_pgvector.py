# api/migrations/0000_enable_pgvector.py
from django.db import migrations

class Migration(migrations.Migration):
    # Make sure this runs before 0001_initial
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
    ]
