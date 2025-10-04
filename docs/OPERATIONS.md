
# ⚙️ DocuChat Operations Guide

## Overview
This document describes how to build, run, test, and monitor the **DocuChat MVP** system — including backend (Django + Channels), frontend (React + Vite), Redis, PostgreSQL, and NGINX reverse proxy.

The setup enables local development and full end-to-end testing using `docker compose up`.

---

## 🧩 Architecture Summary

| Service | Purpose | Port |
|----------|----------|------|
| **nginx** | Reverse proxy serving frontend (`/`) and proxying `/api` and `/ws` | 80 |
| **frontend** | React (Vite) web UI for login, uploads, and chat | 5173 (dev only) |
| **backend** | Django REST API + Channels for WebSocket progress | 8000 |
| **postgres** | Stores user info, document metadata, and embeddings | 5432 |
| **redis** | Backend WebSocket + async task channel layer | 6379 |

All containers share a single Docker network and communicate internally via service names.

---

## 🧱 1. Prerequisites

Install these on your host:
- 🐳 **Docker** ≥ 24.0
- 🧱 **Docker Compose** ≥ 2.20
- 📦 Optional: Node 20+ and Yarn (for local frontend dev)
- 🧰 Optional: `curl`, `psql`, and `make`

---

## 🌍 2. Environment Variables

All backend configuration is loaded from `.env` inside the `backend/` directory.

Create `backend/.env`:

```bash
# Django
DJANGO_SECRET_KEY=dev-secret-not-for-prod
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
POSTGRES_DB=docuchat
POSTGRES_USER=docu
POSTGRES_PASSWORD=docu
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# OpenAI
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini

# OIDC (mock mode for MVP)
OIDC_VERIFY=mock
OIDC_ISSUER=
OIDC_AUDIENCE=docuchat-client
````

> 💡 For local testing, `OIDC_VERIFY=mock` disables real Keycloak validation and accepts any token.

---

## 🚀 3. Starting the System

From the `infra/` folder:

```bash
docker compose up --build
```

This will:

* Start **PostgreSQL** and **Redis**
* Run Django migrations automatically
* Start the **backend** on port `8000`
* Serve the **frontend** through **NGINX** on port `80`

Access the app at:

```
http://localhost
```

You should see the **Login page**.

---

## 🧪 4. Testing the Setup

### Health Check

```bash
curl http://localhost/api/health
```

Expected response:

```json
{ "status": "ok" }
```

### Authentication (Mock Mode)

```bash
curl -H "Authorization: Bearer testtoken" http://localhost/api/me
```

Expected response:

```json
{ "username": "mockuser", "auth_mode": "mock" }
```

### Upload Documents

```bash
curl -X POST http://localhost/api/upload \
  -H "Authorization: Bearer testtoken" \
  -F "files=@example.pdf"
```

Expected response:

```json
{ "status": "queued", "num_files": 1 }
```

### Ask a Question

```bash
curl -X POST http://localhost/api/chat/ask \
  -H "Authorization: Bearer testtoken" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my document about?"}'
```

Expected response:

```json
{
  "answer": "Your document discusses...",
  "citations": [
    { "filename": "example.pdf", "score": 0.87 }
  ]
}
```

---

## 📡 5. WebSocket Monitoring

Progress updates are broadcast via WebSocket:

```
ws://localhost/ws/progress
```

Sample messages:

```json
{ "event": "UPLOAD_STARTED", "filename": "file.pdf" }
{ "event": "TEXT_EXTRACTED", "filename": "file.pdf", "chunks": 42 }
{ "event": "INDEXING_COMPLETE", "filename": "file.pdf" }
```

The frontend displays these updates in the progress section of the Upload page.

---

## 🔄 6. Database & Migrations

### Run Migrations Manually

```bash
docker compose exec backend python manage.py migrate
```

### Inspect Migration State

```bash
docker compose exec backend python manage.py showmigrations
```

### Open PostgreSQL Shell

```bash
docker compose exec postgres psql -U docu -d docuchat
```

---

## 🧰 7. Maintenance Commands

### View Backend Logs

```bash
docker compose logs -f backend
```

### Rebuild All Services

```bash
docker compose down -v
docker compose up --build
```

### Clean Containers & Volumes

```bash
docker system prune -af --volumes
```

---

## 🔐 8. Production Notes

* **NGINX** serves all traffic on port `80`

  * `/` → React build
  * `/api/` → Django backend
  * `/ws/` → WebSocket proxy
* **SSL** can be enabled using `nginx:alpine` + certbot if deploying externally.
* Use a real Keycloak realm once `OIDC_VERIFY=on`.

---

## 🧩 9. Troubleshooting

| Symptom             | Likely Cause                              | Fix                                                        |
| ------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| 403 on `/api/me`    | Missing or invalid token                  | Set `OIDC_VERIFY=mock` or provide valid Bearer token       |
| Upload stuck        | Missing Redis or Celery worker            | Ensure `redis` container is up                             |
| `daphne: not found` | Missing ASGI server in backend Dockerfile | Add `RUN pip install daphne`                               |
| `404 /api/health`   | `health` URL not defined                  | Ensure `path('api/health', HealthView.as_view())` exists   |
| NGINX shows 403     | Missing `index.html`                      | Ensure frontend build is copied to `/usr/share/nginx/html` |

---

## 🧾 10. Verification for Submission

✅ **Checklist for MVP Acceptance**

| Step                     | Command / Check                                    | Status |
| ------------------------ | -------------------------------------------------- | ------ |
| Auth works               | `/api/me` returns mock user                        | ✅      |
| Upload works             | `/api/upload` returns 202                          | ✅      |
| RAG ask works            | `/api/chat/ask` returns answer                     | ✅      |
| WebSocket progress works | Events stream via `/ws/progress`                   | ✅      |
| Frontend works           | NGINX serves app                                   | ✅      |
| Docker                   | `docker compose up` starts all                     | ✅      |
| Documentation            | `ARCHITECTURE.md`, `API.md`, `OPERATIONS.md`, ADRs | ✅      |




