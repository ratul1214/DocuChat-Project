# backend/api/views.py
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from typing import List
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from .serializers import DocumentSerializer, AskSerializer
from .models import Document
from .indexing import index_file_async
from .embeddings import Embedder
from .rag import search
EMBEDDER = Embedder()
from django.http import JsonResponse
# 👇 If you have a Document model, import it. Otherwise this still runs without it.
try:
    from .models import Document
except Exception:
    Document = None


class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return JsonResponse({"status": "ok"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        return Response({'sub': sub})


class DocumentsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        docs = Document.objects.filter(owner_sub=sub).order_by('-created_at')
        return Response(DocumentSerializer(docs, many=True).data)


class UploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail': 'No files uploaded'}, status=400)
        if len(files) > settings.MAX_UPLOAD_FILES:
            return Response({'detail': f'Max {settings.MAX_UPLOAD_FILES} files'}, status=400)

        for f in files:
            content = f.read()
            index_file_async(sub, f.name, content, f.content_type or 'application/octet-stream')
        return Response({'status': 'queued', 'count': len(files)})

def _call_llm(prompt: str) -> str:
    # Minimal: use OpenAI if key present else return deterministic mock
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return '[MOCK ANSWER] This is a placeholder answer generated without external LLM.'
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    chat = client.chat.completions.create(
        model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
        messages=[{'role': 'system', 'content': 'You are a helpful RAG assistant.'}, {'role': 'user', 'content': prompt}],
        temperature=0.2,
    )
    return chat.choices[0].message.content.strip()

class AskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = getattr(request.user, 'oidc_sub', 'mock-user')
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', settings.TOP_K)

        qvec = EMBEDDER.embed([question])[0]
        results = search(sub, qvec, top_k)

        # Build prompt with citations
        context_blocks = []
        citations = []
        for i, (chunk, score) in enumerate(results, start=1):
            context_blocks.append(f"[Doc {i}] {chunk.text}")
            citations.append({
                'index': i,
                'document_id': chunk.document.id,
                'filename': chunk.document.filename,
                'score': round(float(score), 4),
            })
        prompt = (
                'Answer the question using only the context. Cite sources using [Doc i].\n\n' +
                '\n\n'.join(context_blocks) +
                f"\n\nQuestion: {question}\nAnswer:"
        )

        answer = _call_llm(prompt)
        return Response({'answer': answer, 'citations': citations})
