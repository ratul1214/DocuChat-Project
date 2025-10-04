from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

class Document(models.Model):
    owner_sub = models.CharField(max_length=255)  # OIDC subject
    filename = models.CharField(max_length=512)
    content_type = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    owner_sub = models.CharField(max_length=255)
    idx = models.IntegerField()
    text = models.TextField()
    embedding = models.JSONField()  # list[float]

class ChatSession(models.Model):
    owner_sub = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255, blank=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20)  # 'user' | 'assistant' | 'system'
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
