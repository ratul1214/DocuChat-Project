from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import Tenant, AppUser, Document, Chunk

class AcceptanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(key="demo", name="Demo Tenant")
        self.user_sub = "alice"
        self.token = f"mock:{self.tenant.key}:{self.user_sub}"
        self.headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.token}",
            "HTTP_X_TENANT": self.tenant.key,
        }

    def test_login_success(self):
        """✅ Step 1: open login works and returns mock token"""
        resp = self.client.post("/api/auth/login/", {"username": "alice", "password": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.json())

    def test_upload_and_index(self):
        """✅ Step 2: file upload triggers indexing"""
        file = SimpleUploadedFile("sample.txt", b"Hello world this is a test document.")
        resp = self.client.post("/api/upload", {"file": file}, **self.headers)
        self.assertIn(resp.status_code, (200, 201, 202))
        self.assertTrue(Document.objects.exists())

    def test_chat_ask(self):
        """✅ Step 3: chat ask returns an answer (cached LLM stub or real)"""
        prompt = "Summarize hello world"
        resp = self.client.post("/api/chat/ask", {"prompt": prompt}, **self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertTrue(data["answer"])
