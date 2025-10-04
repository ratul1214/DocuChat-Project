from django.contrib import admin
from .models import Document, Chunk, ChatSession, ChatMessage
admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
