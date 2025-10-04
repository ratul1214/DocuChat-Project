from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ProgressConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Expect querystring like ?sub=<subject>
        self.sub = self.scope['query_string'].decode().split('sub=')[-1] or 'mock-user'
        self.group_name = f"progress.{self.sub}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def progress_message(self, event):
        await self.send_json(event['payload'])
