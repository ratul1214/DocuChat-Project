
# 🧠 DocuChat — Document-Aware Chat System (MVP)

**DocuChat** is a minimal **Retrieval-Augmented Generation (RAG)** system that allows authenticated users to upload documents, track indexing progress in real time, and ask questions that are answered with citations to their own documents.

This project is designed as a **3-day MVP** for the assignment:
> “As an authenticated user, I can upload docs, see indexing progress, and ask questions that are answered with citations to my docs.”

---

## 🗂️ Table of Contents

1. [Overview](#overview)
2. [User Story & Requirements](#user-story--requirements)
3. [System Architecture](#system-architecture)
4. [Key Features](#key-features)
5. [Setup & Run](#setup--run)
6. [API Overview](#api-overview)
7. [Frontend Pages](#frontend-pages)
8. [ADRs (Architecture Decision Records)](#adrs-architecture-decision-records)
9. [Tech Stack](#tech-stack)
10. [Project Structure](#project-structure)
11. [MVP Verification Checklist](#mvp-verification-checklist)
12. [Contributors](#contributors)
13. [License](#license)

---

## 🧩 Overview

DocuChat integrates **document storage**, **vector search**, and **LLM question-answering** into a single local environment powered by **Docker Compose**.

Users can:
- Log in using Keycloak or mock tokens
- Upload up to 20 documents (PDF, TXT, DOCX)
- Track upload & indexing progress via WebSocket events
- Ask questions answered from their own document embeddings
- View the response along with **citations** to the original document chunks

---

## 🎯 User Story & Requirements

> **User Story:**  
> “As an authenticated user, I can upload docs, see indexing progress, and ask questions that are answered with citations to my docs.”

### ✅ Must-Haves
1. **Auth:** Login via Keycloak (mock for local dev)
2. **Upload & Index:** Text extraction, chunking, and embedding storage
3. **RAG Ask:** Retrieve top-k chunks, call LLM, return answer with citations
4. **Realtime:** WebSocket progress updates
5. **UI:** Login, Upload, and Chat pages
6. **Docker:** `docker compose up` brings up everything (backend, frontend, db, redis, nginx)
7. **CI:** Linting, tests, and type checks

### 💡 Nice-to-Haves
- Streaming responses via WebSocket  
- Role-based access control  
- Rate limiting

---

## 🏗️ System Architecture

**Layers:**

- **Frontend:** React (Vite) single-page app served via NGINX  
- **Backend:** Django REST Framework + Channels for ASGI  
- **DB:** PostgreSQL for metadata + embeddings  
- **Cache:** Redis for async events and WebSockets  
- **LLM Service:** OpenAI GPT-4o-mini for question answering  
- **Vector Embedding:** `text-embedding-3-small`

See detailed diagram and explanation in [`ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## ✨ Key Features

| Feature | Description |
|----------|--------------|
| 🔑 Authentication | Keycloak JWT validation (mock in local mode) |
| 📤 Upload | Upload ≤20 files, auto-indexed with progress events |
| 🧠 RAG Query | Retrieve top-k embeddings and query LLM |
| ⚡ Realtime | WebSocket `/ws/progress` stream for UI updates |
| 📄 Citations | LLM answers include source document chunks |
| 🐳 Dockerized | Single-command startup via `docker compose up` |
| 🔍 Logs & Health | `/api/health` and structured logs for all services |

---

## 🧱 Setup & Run

### 1. Clone and Configure
```bash
git clone https://github.com/ratul1214/DocuChat-Project.git
cd DocuChat-Project
````

Create `.env` in `backend/`:

```bash
cp backend/.env.sample backend/.env
```

Edit environment values (see [`OPERATIONS.md`](docs/OPERATIONS.md)).

---

### 2. Build and Run

```bash
docker compose up --build
```

Open:

```
http://localhost
```

---

### 3. Verify

```bash
curl http://localhost/api/health
```

Expected:

```json
{ "status": "ok" }
```

---

## 🔌 API Overview

| Endpoint         | Method | Auth | Description                      |
| ---------------- | ------ | ---- | -------------------------------- |
| `/api/health`    | GET    | ❌    | Service health check             |
| `/api/me`        | GET    | ✅    | Returns authenticated user info  |
| `/api/documents` | GET    | ✅    | Lists uploaded documents         |
| `/api/upload`    | POST   | ✅    | Uploads and indexes new docs     |
| `/api/chat/ask`  | POST   | ✅    | RAG-based Q&A with citations     |
| `/ws/progress`   | WS     | ✅    | Streams upload/indexing progress |

Detailed specifications in [`API.md`](docs/API.md).

---

## 🖥️ Frontend Pages

| Page           | Route     | Description                              |
| -------------- | --------- | ---------------------------------------- |
| **LoginPage**  | `/login`  | Authenticates via Keycloak or mock token |
| **UploadPage** | `/upload` | File uploads with progress bar           |
| **ChatPage**   | `/chat`   | Ask questions, see answers and citations |

Implementation: see `frontend/src/pages/`.

---

## 🧱 ADRs (Architecture Decision Records)

| ID                                            | Title                       | Description                                |
| --------------------------------------------- | --------------------------- | ------------------------------------------ |
| [ADR-001](docs/adr/ADR-001-auth.md)           | Authentication Strategy     | Keycloak + mock fallback                   |
| [ADR-002](docs/adr/ADR-002-proxy-topology.md) | Proxy & Networking Topology | NGINX reverse proxy layout                 |
| [ADR-003](docs/adr/ADR-003-rag-pipeline.md)   | RAG Pipeline Design         | Chunking, embedding, and retrieval process |

---

## 🧰 Tech Stack

| Layer              | Technology                                  |
| ------------------ | ------------------------------------------- |
| **Frontend**       | React (Vite + TypeScript)                   |
| **Backend**        | Django REST Framework, Channels, Daphne     |
| **Database**       | PostgreSQL                                  |
| **Cache**          | Redis                                       |
| **Auth**           | Keycloak (OIDC)                             |
| **AI Integration** | OpenAI GPT-4o-mini + text-embedding-3-small |
| **Infrastructure** | Docker Compose + NGINX                      |
| **CI/CD**          | GitHub Actions (lint, typecheck, test)      |

---

## 🧾 Project Structure

```
DocuChat-Project/
├── backend/
│   ├── api/
│   │   ├── views.py
│   │   ├── models.py
│   │   ├── urls.py
│   ├── backend/
│   │   ├── settings.py
│   │   ├── urls.py
│   └── manage.py
├── frontend/
│   ├── src/pages/
│   ├── src/AppRouter.tsx
│   ├── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── OPERATIONS.md
│   └── adr/
│       ├── ADR-001-auth.md
│       ├── ADR-002-proxy-topology.md
│       └── ADR-003-rag-pipeline.md
├── infra/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── Dockerfile
└── README.md
```

---

## ✅ MVP Verification Checklist

| Step | Description                         | Status |
| ---- | ----------------------------------- | ------ |
| 1    | Auth works (`/api/me`)              | ✅      |
| 2    | File upload works                   | ✅      |
| 3    | Indexing progress visible           | ✅      |
| 4    | RAG chat returns answer             | ✅      |
| 5    | WebSocket events                    | ✅      |
| 6    | Frontend served via NGINX           | ✅      |
| 7    | `docker compose up` one-step deploy | ✅      |
| 8    | Docs (README, API, ADRs, etc.)      | ✅      |

---



## 🪪 License

This project is released under the **MIT License**.
See the `LICENSE` file for details.

---

> 🧠 *"Knowledge becomes powerful when it is connected."*
> — DocuChat Team, 2025


