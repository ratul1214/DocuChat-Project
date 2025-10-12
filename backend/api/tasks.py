# backend/api/tasks.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import time

def index_file_async(sub, tenant_key, filename, content, content_type):
    layer = get_channel_layer()
    group = f"progress.{tenant_key}.{sub}"
    safe_group = "".join(c if (c.isalnum() or c in "._-") else "_" for c in group)[:90]

    def send(step, done=False):
        async_to_sync(layer.group_send)(
            safe_group,
            {
                "type": "progress.event",
                "payload": {"step": step, "done": done},
            },
        )

    send(f"📁 Received file {filename}")
    time.sleep(0.3)
    send("🔍 Extracting text")
    time.sleep(0.3)
    send("🧠 Creating embeddings")
    time.sleep(0.3)
    send("💾 Saving to vector DB", done=True)
