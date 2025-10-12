# backend/api/consumers.py
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncJsonWebsocketConsumer

def _sanitize_group(s: str) -> str:
    # only ASCII alnum, dot, underscore, hyphen; max 90 chars
    return "".join(c if (c.isalnum() or c in "._-") else "_" for c in s)[:90]

class ProgressConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # query: ?tenant=default&sub=mock-user
        qs = parse_qs((self.scope.get("query_string") or b"").decode())
        tenant = (qs.get("tenant", ["default"])[0] or "default")
        sub    = (qs.get("sub",    ["anon"])[0] or "anon")
        self.group = _sanitize_group(f"progress.{tenant}.{sub}")
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"message": f"joined {self.group}"})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def progress_event(self, event):
        # event: {"type":"progress.event","payload":{...}}
        await self.send_json(event["payload"])


class AgentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # query: ?tenant=default&report_id=123
        qs = parse_qs((self.scope.get("query_string") or b"").decode())
        tenant    = (qs.get("tenant",    ["default"])[0] or "default")
        report_id = (qs.get("report_id", [""])[0] or "")
        self.group = _sanitize_group(f"agent.{tenant}.{report_id}")
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"message": f"joined {self.group}"})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def agent_event(self, event):
        # event: {"type":"agent.event","payload":{...}}
        await self.send_json(event["payload"])
