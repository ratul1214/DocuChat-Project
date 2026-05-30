# DocuChat — Document-Aware Chat System 

**DocuChat** is an extended **Retrieval-Augmented Generation (RAG)** system that now supports multi-tenant document access, background indexing progress via WebSocket, and an LLM-powered chat interface. This builds upon the Step 1 MVP by adding deeper backend functionality, agent report generation, and observability.

This project completes :
> “As an authenticated user, I can upload docs, see indexing progress, and ask questions that are answered with citations to my docs — across multiple tenants, with metrics and LLM integration.”

---

## Table of Contents

1. [Overview](#overview)
2. [New Additions in Step 2](#new-additions-in-step-2)
3. [User Story & Requirements](#user-story--requirements)
4. [System Architecture](#system-architecture)
5. [Key Features](#key-features)
6. [Setup & Run](#setup--run)
7. [API Overview](#api-overview)
8. [Frontend Pages](#frontend-pages)
9. [ADRs (Architecture Decision Records)](#adrs-architecture-decision-records)
10. [Tech Stack](#tech-stack)
11. [Project Structure](#project-structure)
12. [Verification Checklist](#verification-checklist)
13. [Submission Notes](#submission-notes)

---

## 🧩 Overview

DocuChat integrates **document storage**, **vector search**, and **LLM-based Q&A** into one containerized application. In Step 2, the system evolves into a multi-tenant environment with persistent reports, Prometheus metrics, and improved WebSocket progress tracking.

Users can:
- Log in with mock credentials per tenant
- Upload and index documents
- See progress updates in real time via WebSocket
- Ask questions answered with context-aware document citations
- Generate background agent reports
- Monitor metrics via `/metrics`

---

## New Additions in Step 2

| Area | Improvement |
|------|--------------|
| Multi-Tenancy | Documents, users, and embeddings are tenant-isolated |
| Progress Streaming | Improved `/ws/progress` event structure with tenant & sub-user keys |
| Agent Reports | Background task generation and async agent status updates |
| Metrics | Added Prometheus `/metrics` endpoint (request and vector metrics) |
| Authentication | Token-based mock login (`/api/auth/login`) |
| LLM Integration | Fallback to mock or real OpenAI backend |
| Database | Clean migrations with `Tenant`, `AppUser`, and `Report` models |

---

## 🎯 User Story & Requirements

> **Step 2 User Story:**
> “As an authenticated user, I can upload docs, see indexing progress, and ask questions that are answered with citations to my docs — in an isolated tenant environment.”

### ✅ Must-Haves
1. Multi-tenant authentication
2. Document upload + async indexing with progress
3. `/api/chat/ask` endpoint using embeddings + LLM
4. Background report agent system
5. Prometheus metrics endpoint
6. Docker Compose orchestration (backend, frontend, Redis, Postgres, Nginx)

### 💡 Nice-to-Haves
- Live LLM streaming responses
- Role-based tenant access control
- Multi-step agent execution logging

---

## System Architecture

**Layers:**

- **Frontend:** React + Vite app with WebSocket progress visualization
- **Backend:** Django REST Framework + Channels for ASGI
- **Database:** PostgreSQL (with `pgvector` extension)
- **Cache:** Redis for async tasks and pub/sub WebSocket events
- **LLM Service:** OpenAI GPT or mock fallback
- **Metrics:** Prometheus-compatible `/metrics` endpoint

---

## ✨ Key Features

| Feature | Description |
|----------|--------------|
| Authentication | Simple mock token system per tenant |
| Tenant Isolation | Each user and document linked to a tenant |
| Upload | Multi-file uploads, async indexing, real-time updates |
| Chat Ask | Context-aware answers with citations |
| WebSocket | `/ws/progress` and `/ws/agent` for live updates |
| Metrics | Prometheus `/metrics` output with query timing |
| Agent Reports | Async threaded report generation with `/api/agent/report` |
| Dockerized | Full stack managed via `docker compose up` |

---

## 🧱 Setup & Run

### 1. Clone and Configure
```bash
git clone https://github.com/ratul1214/DocuChat-Project.git
cd DocuChat-Project
cp backend/.env.sample backend/.env
cp frontend/.env.sample frontend/.env
cd infra
docker compose up --build
docker compose exec backend python manage.py makemigrations api -n initial
docker compose exec backend python manage.py migrate

````


Edit environment values (especially your own OPENAI_API_KEY) (see [`OPERATIONS.md`](docs/OPERATIONS.md)).

---


Open:

Access via:
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

| Endpoint | Method | Auth | Description |
|-----------|--------|------|--------------|
| `/api/auth/login` | POST | ❌ | Mock login for tenant user |
| `/api/me` | GET | ✅ | Returns tenant & sub-user info |
| `/api/upload` | POST | ✅ | Uploads and indexes new docs |
| `/api/documents` | GET | ✅ | List of uploaded docs (tenant-scoped) |
| `/api/chat/ask` | POST | ✅ | Ask questions with RAG context |
| `/api/agent/report` | POST | ✅ | Start background report task |
| `/api/reports` | GET | ✅ | List generated reports |
| `/metrics` | GET | ❌ | Prometheus metrics endpoint |
| `/ws/progress` | WS | ✅ | Upload progress updates |
| `/ws/agent` | WS | ✅ | Report generation progress |

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|-------|--------|--------------|
| **Login** | `/login` | Tenant-based mock authentication |
| **Upload** | `/upload` | File uploads with real-time progress |
| **Chat** | `/chat` | Ask questions, view answers & citations |
| **Reports** | `/reports` | View background agent-generated reports |

---

## 🧱 ADRs (Architecture Decision Records)

| ID | Title | Description |
|----|--------|-------------|
| [ADR-001](docs/adr/ADR-001-auth.md) | Authentication Strategy | Mock + JWT fallback |
| [ADR-002](docs/adr/ADR-002-proxy-topology.md) | Proxy Layout | NGINX reverse proxy & port mapping |
| [ADR-003](docs/adr/ADR-003-rag-pipeline.md) | RAG Pipeline | Chunking, embedding, and retrieval |
| [ADR-004](docs/adr/ADR-004-multi-tenancy.md) | Tenant Isolation | Tenant key resolution and model linkage |

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| **Frontend** | React + Vite + TypeScript |
| **Backend** | Django REST Framework + Channels |
| **Database** | PostgreSQL + pgvector |
| **Cache** | Redis |
| **LLM** | OpenAI GPT (real or mock fallback) |
| **Infrastructure** | Docker Compose + NGINX |
| **Metrics** | Prometheus-compatible endpoint |

---

## 📂 Project Structure

```
DocuChat/
├── backend/
│   ├── api/
│   │   ├── views.py
│   │   ├── models.py
│   │   ├── consumers.py
│   │   ├── indexing.py
│   ├── backend/
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── pages/
├── infra/
│   ├── docker-compose.yml
│   └── nginx/
└── README.md
```

---

## ✅ Verification Checklist

| Step | Description | Status |
|------|--------------|--------|
| 1 | Auth + Tenant isolation | ✅ |
| 2 | Upload & Index with progress | ✅ |
| 3 | Chat Ask (RAG context) | ✅ |
| 4 | Agent Report generation | ✅ |
| 5 | WebSocket events for progress | ✅ |
| 6 | Prometheus metrics endpoint | ✅ |
| 7 | Docker Compose one-step deploy | ✅ |
| 8 | Documentation (README, ADRs, etc.) | ✅ |

---

## 📦 Submission Notes

**Repository Link:**  
[https://github.com/ratul1214/DocuChat-Project.git](https://github.com/ratul1214/DocuChat-Project.git)

**Screen Recording (≤5 min):**
- Login as a tenant user
- Upload documents → view real-time indexing
- Ask a question → see contextual answer
- Generate an agent report
- Show `/metrics` endpoint output

**Quick Run Command:**
```bash
docker compose up --build
```

---

> 🧠 *"Knowledge becomes powerful when it is connected."*
