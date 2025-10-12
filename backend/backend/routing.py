# backend/routing.py
from django.urls import re_path
from api.consumers import ProgressConsumer

websocket_urlpatterns = [
    re_path(r"^ws/progress$", ProgressConsumer.as_asgi()),
]

from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.consumers import ProgressConsumer, AgentConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/progress$", ProgressConsumer.as_asgi()),
            re_path(r"^ws/agent$",    AgentConsumer.as_asgi()),
        ])
    ),
})