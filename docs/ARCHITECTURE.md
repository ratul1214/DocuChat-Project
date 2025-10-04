


# 🏗️ DocuChat System Architecture

## Overview
DocuChat is a full-stack web application that enables authenticated users to upload documents, monitor indexing progress, and ask natural language questions answered with citations drawn from their uploaded content.  
The system follows a modular **microservice-inspired architecture** with separate **frontend**, **backend**, **database**, **cache**, and **reverse proxy** layers—all orchestrated with Docker Compose.

---

## 🧩 High-Level Components

| Layer | Technology | Description |
|-------|-------------|-------------|
| **Frontend** | React + TypeScript + Vite | SPA with routes for login, upload, and chat. Uses Fetch API for REST calls and WebSocket for progress updates. |
| **Backend** | Django + Django REST Framework + Channels | Exposes APIs for authentication, file upload, chat (RAG), and progress streaming. Integrates with Postgres, Redis, and OpenAI. |
| **Database** | PostgreSQL 16 | Stores user data, document metadata, and embeddings. |
| **Cache / Queue** | Redis 7 | Used for WebSocket progress updates and background job coordination. |
| **LLM Integration** | OpenAI (gpt-4o-mini) | Handles natural language questions and contextual RAG responses. |
| **Reverse Proxy** | NGINX | Serves frontend build and reverse-proxies all `/api` and `/ws` requests to the backend. |
| **Container Orchestration** | Docker Compose | Manages all services (frontend, backend, Postgres, Redis, NGINX). |

---

## ⚙️ Backend Architecture

### 1. **API Endpoints**
| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/me` | GET | Returns current authenticated user info. |
| `/api/upload` | POST | Accepts PDF/TXT/MD files for indexing. |
| `/api/documents` | GET | Lists all uploaded documents. |
| `/api/chat/ask` | POST | Accepts a user question, retrieves relevant chunks, and calls LLM. |
| `/api/health` | GET | Simple readiness check. |

### 2. **RAG Pipeline**
```text
PDF/TXT/MD Upload
   ↓
Text Extraction
   ↓
Chunking → Token Overlap (600 / 80)
   ↓
Embedding (text-embedding-3-small)
   ↓
Vector Storage (Postgres or In-memory)
   ↓
Top-K Retrieval
   ↓
LLM Prompt → Answer + Citations
````

Each uploaded document is split into overlapping text chunks.
Each chunk is embedded and stored.
During queries, the top K embeddings are retrieved and passed to the LLM for contextual answering.

### 3. **Real-time Progress (WebSocket)**

* The backend emits progress events (e.g., `UPLOAD_STARTED`, `INDEXING_COMPLETE`) over `/ws/progress`.
* The frontend `ProgressStream` component subscribes to updates for visual feedback.

---

## 🔐 Authentication (OIDC / Mock Mode)

* **OIDC (Keycloak)**: Tokens are validated by Django using `KeycloakOIDCAuthentication`.
* **Mock mode**: For local development (`OIDC_VERIFY=mock`), any Bearer token is accepted.
* Frontend login is handled via a simple password field and stored token in `localStorage`.

---

## 🌐 Proxy Topology (NGINX)

```
            ┌──────────────────────────────┐
            │        React Frontend        │
            │   (served by NGINX /index)   │
            └──────────────┬───────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  NGINX Reverse Proxy   │
               │ /api/* → backend:8000  │
               │ /ws/*  → backend:8000  │
               │ /       → /usr/share/nginx/html │
               └──────────────┬─────────┘
                              │
      ┌───────────────────────────────────────────┐
      │ Backend (Django + Channels + DRF)         │
      └───────────────────────────────────────────┘
                │             │
        ┌───────┴──────┐ ┌───┴────┐
        │ PostgreSQL DB │ │ Redis  │
        └───────────────┘ └────────┘
```

---

## 🐳 Docker Compose Setup

### `infra/docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16
  redis:
    image: redis:7
  backend:
    build: ../backend
    ports: ["8000:8000"]
  nginx:
    image: nginx:1.29
    ports: ["80:80"]
    depends_on:
      - backend
```

Each service runs in its own container and communicates via Docker’s internal network.

---

## 🧠 Data Flow

1. **User Authenticates** → Frontend stores token.
2. **User Uploads File** → Frontend sends to `/api/upload`.
3. **Backend Extracts + Indexes** → Emits progress updates.
4. **Chunks + Embeddings Saved** → In Postgres.
5. **User Asks Question** → `/api/chat/ask` fetches top-K chunks and sends to LLM.
6. **Answer Returned** → With citations.

---

## 🧪 Development & Testing

* Run locally:

  ```bash
  cd infra
  docker compose up --build
  ```
* Access frontend at [http://localhost](http://localhost)
* API directly at [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📂 Directory Structure

```
docuchat/
├── backend/
│   ├── api/
│   ├── backend/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── manage.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/api.ts
│   └── vite.config.ts
├── infra/
│   ├── docker-compose.yml
│   └── nginx.conf
└── docs/
    ├── ARCHITECTURE.md
    └── adr/
```

---

## ✅ Future Enhancements

* Full OIDC login with redirect flow.
* Role-based access control (user/admin).
* Rate limiting per user.
* Persistent vector DB (e.g., pgvector).
* Streaming LLM responses over WebSocket.

---

## 📜 References

* ADR-001: Authentication Strategy
* ADR-002: Proxy Topology
* ADR-003: RAG Pipeline Design


