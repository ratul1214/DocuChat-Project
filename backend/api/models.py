# backend/api/models.py
from django.db import models
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField
from pgvector.django import VectorField

class Tenant(models.Model):
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)

class AppUser(models.Model):
    sub = models.CharField(max_length=128)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    roles = models.JSONField(default=list)

    class Meta:
        unique_together = [("tenant", "sub")]

class Document(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    text = models.TextField()
    section = models.CharField(max_length=255, blank=True, default="")
    page_start = models.IntegerField(blank=True, null=True)
    page_end = models.IntegerField(blank=True, null=True)
    embedding = VectorField(dimensions=1536, null=True)
    tsv = SearchVectorField(null=True)

    class Meta:
        indexes = [models.Index(fields=["tsv"], name="chunk_tsv_idx")]

class ChatTurn(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)
    question = models.TextField()
    answer = models.TextField(blank=True, default="")
    citations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatSession(models.Model):
    owner_sub = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255, blank=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20)  # 'user' | 'assistant' | 'system'
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class Report(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user   = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    title  = models.CharField(max_length=255)
    status = models.CharField(max_length=32, default="queued")  # queued|running|done|error
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
