from django.contrib import admin
from django.urls import path
from api.views import HealthView, MeView, DocumentsView, UploadView, AskView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health', HealthView.as_view(), name='health'),
    path('api/me', MeView.as_view(), name='me'),
    path('api/documents', DocumentsView.as_view(), name='documents'),
    path('api/upload', UploadView.as_view(), name='upload'),
    path('api/chat/ask', AskView.as_view(), name='chat-ask'),
]
