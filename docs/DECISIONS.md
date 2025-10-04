# ADR-001: Authentication Strategy (Keycloak + Mock Mode for Step 1)

**Status:** Accepted  
**Date:** 2025-10-04  
**Step:** 1 (MVP)

## Context
The assignment requires that authentication be implemented using Keycloak (OIDC) for frontend login and Django token validation on the backend.  
However, during Step 1 (MVP), the primary focus is functional flow (upload → index → ask). Setting up Keycloak integration and HTTPS certificates can delay local iteration.

## Decision
- Use **Keycloak** as the long-term authentication provider (Step 2).
- For **Step 1**, enable a **mock OIDC verification** mode via:
  ```bash
  OIDC_VERIFY=mock
  ```
- Django backend uses a custom `KeycloakOIDCAuthentication` class that accepts any Bearer token when `OIDC_VERIFY=mock`.
- Frontend provides a simple password input for users to paste or type a token (mock accepted).

## Consequences
- ✅ Enables quick end-to-end testing without blocking on Keycloak setup.
- ⚠️ Mock mode should **never be used in production**.
- Step 2 will replace the mock with actual OIDC introspection using the Keycloak realm URL:
  ```
  OIDC_ISSUER=https://keycloak:8443/realms/docu
  ```
- Testing and CI will rely on the mock mode.

## Alternatives Considered
- Implementing OIDC in Step 1 → too time-consuming and non-critical for MVP.
- Using Django’s default `SessionAuthentication` → not compatible with SPA + Bearer token.

## References
- Assignment: “Auth: Login via Keycloak from the frontend; Django validates tokens.”
- ADR type: “Auth choices.”

# ADR-002: Reverse Proxy and Service Topology

**Status:** Accepted  
**Date:** 2025-10-04  
**Step:** 1 (MVP)

## Context
The system must run locally using Docker Compose and expose a unified interface via NGINX.  
Requirements include serving:
- `/` → React frontend (SPA)
- `/api` → Django REST API
- `/ws` → WebSocket for progress updates

The backend runs Daphne (ASGI) for Channels and Redis for message passing.

## Decision
- Use **NGINX** as the reverse proxy and static file server.
- Define the routing rules:
  ```nginx
  location / {
    root /usr/share/nginx/html;
    index index.html;
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://backend:8000/;
    proxy_set_header Host $host;
  }

  location /ws/ {
    proxy_pass http://backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
  }
  ```
- Frontend built assets (`/usr/share/nginx/html`) served by NGINX container.
- All services (`backend`, `redis`, `postgres`, `nginx`) orchestrated via `docker-compose.yml`.

## Consequences
- ✅ Clean local environment: `docker compose up` runs everything.
- ✅ SPA routes handled gracefully via `try_files ... /index.html`.
- ⚠️ 404 errors appear if build folder missing — must build frontend before `docker compose up`.
- ⚠️ Future scaling (Step 2) might require moving NGINX config to `nginx.conf.prod`.

## Alternatives Considered
- Serving React directly from Vite dev server → breaks containerized environment.
- Using Caddy instead of NGINX → adds complexity for this scale.

## References
- Assignment Step 1: “Docker compose up runs everything locally; NGINX reverse-proxies /, /api, /ws.”
- ADR type: “Infrastructure / Proxy topology.”

# ADR-003: Retrieval-Augmented Generation (RAG) Pipeline Design

**Status:** Accepted  
**Date:** 2025-10-04  
**Step:** 1 (MVP)

## Context
The MVP must allow authenticated users to upload documents (≤20), index them (extract, chunk, embed), and later query them via `/api/chat/ask` with answers that include citations.  
The system must also stream real-time progress during indexing over WebSockets.

## Decision
- Implement a simple **RAG pipeline** within Django backend:
  1. **Upload** → Accept PDF/Markdown/Text via `/api/upload`.
  2. **Extract** → Convert content to plain text using `PyMuPDF` or `markdown` parser.
  3. **Chunk** → Use sliding window (e.g., 600 tokens, 80 overlap).
  4. **Embed** → Call OpenAI embeddings API (`text-embedding-3-small`).
  5. **Store** → Save chunks + vectors in Postgres or lightweight FAISS index.
  6. **Ask** → Retrieve top-k (default 5) via cosine similarity; feed to LLM (`gpt-4o-mini`).
  7. **Respond** → Return answer text and citations (filename, similarity score).

- Environment variables:
  ```bash
  OPENAI_API_KEY=...
  EMBEDDING_MODEL=text-embedding-3-small
  LLM_MODEL=gpt-4o-mini
  TOP_K=5
  ```

- Progress messages sent via Django Channels (Redis backend).

## Consequences
- ✅ Fully functional MVP RAG loop (upload → ask → cite).
- ✅ Extensible for Step 2 (multi-user vector stores, caching).
- ⚠️ Indexing happens synchronously — may block on large uploads.
- ⚠️ Local embeddings incur API cost; can be swapped for open-source model later.

## Alternatives Considered
- Using managed vector DB (Pinecone, Weaviate) → overkill for Step 1.
- Storing embeddings in memory → ephemeral; lost on restart.

## References
- Assignment Step 1: “Upload ≤20 files, extract text, chunk, store embeddings; /api/chat/ask retrieves top-k and returns answer with citations.”
- ADR type: “Retrieval strategy.”
