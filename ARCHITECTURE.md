<!-- last_verified: 2026-07-29 -->
# Architecture

ColPali PDF Search is a self-hosted visual document search app. It retrieves the
right *page* of a PDF corpus using ColPali vision embeddings over rendered page
images — no OCR, no text extraction. Backblaze B2 (S3-compatible API) is the
single storage layer; the only credentials are `B2_*` (the model runs locally).

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with corpus + storage stats
  - Ingest (`/ingest`), Library (`/library`), document detail (`/documents/[id]`)
  - Visual Search (`/search`)
  - Full-bucket File Browser (`/files`) and generic Upload (`/upload`) from the starter
- **services/api/** — FastAPI backend (layered architecture)
  - PDF render → page PNGs; ColPali embedding; FAISS index build + MaxSim search
  - Document CRUD; corpus stats; B2 S3 integration via boto3
  - Health check, structured JSON logging, Prometheus-format metrics
- **packages/shared/** — TypeScript type definitions mirroring the Pydantic models

## Backend Layering

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access + external SDKs (boto3, torch/colpali, faiss, fitz)
  |
service/   Business logic — calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules
1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (service must not import from runtime)
3. `boto3` only allowed in `repo/` — verified by `tests/test_structure.py`
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### External SDK containment
`torch` / `colpali-engine` / `transformers`, `faiss`, and `fitz` (PyMuPDF) are
imported **lazily inside the repo/ functions** that use them, so importing the
app (and the structural + contract tests) never pulls in the multi-GB ML stack
and no model weights are downloaded during the build.

### Directory Structure
```
services/api/app/
  types/       Pydantic models (Document, SearchResponse, CorpusStats, FileMetadata, ...)
  config/      Settings loaded from environment (B2_*, COLPALI_*, HF_TOKEN)
  repo/        b2_client.py, b2_object.py, store.py, pdf_render.py, colpali.py, faiss_index.py, counter.py
  service/     documents.py, ingest.py, search.py, files.py, upload.py, metadata.py
  runtime/     documents.py, search.py, files.py, upload.py, health.py, metrics.py, ratelimit.py
```

## Data Stores — Backblaze B2 (sole store, no database)

S3-compatible API only (no b2-native). Object layout:

- `pages/<doc-id>/<n>.png` — rendered page images
- `embeddings/<doc-id>/<n>.npy` — per-page ColPali multi-vector embeddings
- `index/index.faiss` + `index/mapping.json` — FAISS index + row→page map
- `documents/<doc-id>/meta.json` — document record (title, page_count, dpi, model, status, byte counts, timestamps)
- `uploads/<name>` — objects from the starter's generic upload

S3 operations: `put_object`, `get_object`, `list_objects_v2` (paginated,
full-bucket and `documents/`-scoped), `head_bucket` (health),
`delete_objects` (prefix-scoped purge), `generate_presigned_url` (serve page
images). The S3 endpoint is derived from `B2_REGION`; no region string is
hardcoded in source.

## External Services

- **Backblaze B2 S3 API** — storage, retrieval, deletion, presigned URLs
- **ColPali** (`colpali-engine`) — runs **locally**, CPU by default with CUDA
  autodetect. No external provider key. `HF_TOKEN` is an optional one-time
  model-download token for the gated PaliGemma base only.

## Data Flows

- **Ingest (create)**: Browser -> `POST /documents` -> render pages (fitz) ->
  `put_object` page PNGs -> write `meta.json` (status `rendered`)
- **Index (run)**: Browser -> `POST /documents/{id}/index` -> load pages from B2
  -> `embed_images` (ColPali) -> `put_object` `.npy` -> rebuild FAISS ->
  `put_object` index + mapping -> status `indexed`
- **Search**: Browser -> `GET /search?q=` -> load index from B2 -> `embed_query`
  -> MaxSim rank -> presigned page URLs + scores
- **Read/Edit/Delete**: `GET/PATCH/DELETE /documents/{id}` -> service -> B2
  (delete is scoped to the document's own prefixes, then the index is rebuilt)

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md). CORS is registered LAST (outermost) so
every response — including error 500s — carries CORS headers. A per-IP
rate-limit middleware sits inner to CORS. Document and search routes are
unauthenticated and corpus-wide (single-tenant demo stance).

## Observability
- Structured JSON logging with `request_id`
- Request timing middleware (also the catch-all that maps uncaught exceptions to a typed 500)
- `/metrics` (Prometheus format) and `/health` (B2 connectivity check)

## API Contract
- Checked-in OpenAPI artifact: `docs/api/openapi.json`
- Export/check: `pnpm contract:export` / `pnpm contract:check`
- FastAPI freshness test: `services/api/tests/test_openapi_contract.py`
- Frontend route drift test: `apps/web/src/lib/api-contract.test.ts`
- `GET /metrics` is intentionally server-only.

## Canonical Files
- Visual embedding: `services/api/app/repo/colpali.py`
- FAISS index + MaxSim: `services/api/app/repo/faiss_index.py`
- PDF render: `services/api/app/repo/pdf_render.py`
- Generic B2 object ops: `services/api/app/repo/store.py`
- Ingest orchestration: `services/api/app/service/ingest.py`
- Search orchestration: `services/api/app/service/search.py`
- Pydantic models: `services/api/app/types/`
- Config: `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`

## Core Features
- [Document Ingest](docs/features/document-ingest.md)
- [ColPali Embedding](docs/features/colpali-embedding.md)
- [FAISS Index](docs/features/faiss-index.md)
- [Visual Search](docs/features/visual-search.md)
- [Document Library](docs/features/document-library.md)
- [Dashboard](docs/features/dashboard.md)
- [File Browser](docs/features/file-browser.md)

## References
- [docs/SECURITY.md](docs/SECURITY.md) — security principles
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
