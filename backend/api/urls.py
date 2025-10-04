from django.urls import path
from .views import UploadView, AskView, MeView, ListDocumentsView
# backend/core/urls.py
from django.urls import path
from .views import health

urlpatterns = [
    path("health/", health),
]

urlpatterns = [
    path('me', MeView.as_view(), name='me'),
    path('documents', ListDocumentsView.as_view(), name='documents'),
    path('upload', UploadView.as_view(), name='upload'),
    path('chat/ask', AskView.as_view(), name='chat-ask'),
]
from .views import UploadView, AskView, MeView, ListDocumentsView, health

urlpatterns = [
    path('me', MeView.as_view(), name='me'),
    path('documents', ListDocumentsView.as_view(), name='documents'),
    path('upload', UploadView.as_view(), name='upload'),
    path('chat/ask', AskView.as_view(), name='chat-ask'),
    path('health', health, name='health'),          # ← add this
    path('health/', health),                        # ← optional, trailing slash
]
