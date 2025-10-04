


# 📘 DocuChat API Specification

## Overview
This document defines the REST API endpoints for **DocuChat**, an authenticated document question-answering system.

All endpoints are served from:

```

[http://localhost:8000/api/](http://localhost:8000/api/)

```

or via NGINX reverse proxy:

```

[http://localhost/api/](http://localhost/api/)

```

All endpoints require an **Authorization Bearer Token** header unless otherwise noted.

---

## 🔐 Authentication

### `GET /api/me`
Returns the current authenticated user's information.

#### Headers
```

Authorization: Bearer <token>

````

#### Response
```json
{
  "username": "mockuser",
  "email": "mock@docuchat.local",
  "auth_mode": "mock"
}
````

#### Example

```bash
curl -X GET http://localhost:8000/api/me \
  -H "Authorization: Bearer testtoken"
```

---

## 📁 Document Management

### `GET /api/documents`

Lists all uploaded documents for the authenticated user.

#### Headers

```
Authorization: Bearer <token>
```

#### Response

```json
[
  {
    "id": 1,
    "filename": "example.pdf",
    "created_at": "2025-10-04T10:24:15Z",
    "status": "indexed",
    "num_chunks": 32
  }
]
```

#### Example

```bash
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer testtoken"
```

---

### `POST /api/upload`

Uploads one or more files (PDF, TXT, MD) for text extraction and indexing.

#### Headers

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

#### Body

Form-data:

* `files`: Multiple file fields allowed (max 20).

#### Response

```json
{
  "status": "queued",
  "num_files": 2,
  "message": "Files queued for indexing."
}
```

#### Example

```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer testtoken" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.txt"
```

---

## 💬 Chat (RAG-based Q&A)

### `POST /api/chat/ask`

Accepts a user question, retrieves top-k relevant chunks using embeddings, and returns an LLM-generated answer with citations.

#### Headers

```
Authorization: Bearer <token>
Content-Type: application/json
```

#### Body

```json
{
  "question": "What are the main challenges mentioned in my uploaded reports?",
  "top_k": 5
}
```

#### Response

```json
{
  "answer": "Your reports mention that supply chain delays and data quality issues are the main challenges.",
  "citations": [
    {
      "index": 1,
      "filename": "Q2_Report.pdf",
      "score": 0.89
    },
    {
      "index": 2,
      "filename": "Market_Notes.txt",
      "score": 0.83
    }
  ]
}
```

#### Example

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Authorization: Bearer testtoken" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the summary of my project proposal?", "top_k": 3}'
```

---

## 📡 Realtime Progress (WebSocket)

### `GET /ws/progress`

WebSocket endpoint for monitoring upload and indexing progress.

#### Connection Example (JavaScript)

```js
const ws = new WebSocket("ws://localhost/ws/progress");
ws.onmessage = (e) => console.log("Progress event:", e.data);
```

#### Typical Event Payloads

```json
{ "event": "UPLOAD_STARTED", "filename": "report.pdf" }
{ "event": "TEXT_EXTRACTED", "filename": "report.pdf", "chunks": 24 }
{ "event": "INDEXING_COMPLETE", "filename": "report.pdf" }
```

---

## ❤️ Health Check

### `GET /api/health`

Simple health endpoint for deployment readiness.

#### Response

```json
{ "status": "ok" }
```

#### Example

```bash
curl http://localhost:8000/api/health
```

---

## 🧱 HTTP Status Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| 200  | Success                              |
| 201  | Created                              |
| 202  | Accepted (for queued uploads)        |
| 400  | Bad Request                          |
| 401  | Unauthorized (missing/invalid token) |
| 403  | Forbidden (CORS or auth error)       |
| 404  | Not Found                            |
| 500  | Internal Server Error                |

---

## 🧩 Example Workflow

1. **Login / Mock Auth**

   ```bash
   curl http://localhost:8000/api/me -H "Authorization: Bearer testtoken"
   ```

2. **Upload Files**

   ```bash
   curl -X POST http://localhost:8000/api/upload \
     -H "Authorization: Bearer testtoken" \
     -F "files=@report.pdf"
   ```

3. **Check Documents**

   ```bash
   curl -X GET http://localhost:8000/api/documents \
     -H "Authorization: Bearer testtoken"
   ```

4. **Ask a Question**

   ```bash
   curl -X POST http://localhost:8000/api/chat/ask \
     -H "Authorization: Bearer testtoken" \
     -H "Content-Type: application/json" \
     -d '{"question": "Summarize my Q2 data analysis"}'
   ```

5. **Monitor Progress**

   * Connect WebSocket client to `ws://localhost/ws/progress`.

---

## ⚙️ Notes for Developers

* Max 20 files per upload (`MAX_UPLOAD_FILES`).
* Token-based mock auth enabled when `OIDC_VERIFY=mock`.
* Default embedding model: `text-embedding-3-small`.
* Default LLM: `gpt-4o-mini`.

---

## 🔒 Security Considerations

* All endpoints require Bearer token auth (mock or Keycloak).
* NGINX enforces same-origin headers.
* CSRF disabled for API endpoints (token-based auth only).

---

## 📚 Future Extensions

* Implement refreshable OIDC tokens with Keycloak.
* Add `/api/admin/metrics` for indexing statistics.
* Add rate limiting and role-based permissions.

---




