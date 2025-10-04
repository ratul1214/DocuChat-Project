from rest_framework import serializers
from .models import Document, Chunk

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'filename', 'content_type', 'created_at']

class AskSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False)
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False)
