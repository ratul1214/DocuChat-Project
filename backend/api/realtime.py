# backend/api/realtime.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def send_progress(sub: str, stage: str, message: str, extra: dict | None = None):
    """
    Emits a progress event to the user's WS group: progress.<sub>
    """
    group = f"progress.{sub}"
    payload = {"stage": stage, "message": message}
    if extra:
        payload.update(extra)

    ch = get_channel_layer()
    async_to_sync(ch.group_send)(group, {
        "type": "progress.event",  # must match consumer method name: progress_event
        "payload": payload,
    })
