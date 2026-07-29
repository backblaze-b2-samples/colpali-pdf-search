<!-- last_verified: 2026-07-29 -->
# Feature: ColPali Embedding

## Purpose
Embed each rendered page image into a ColPali multi-vector (late-interaction)
embedding and store those vectors in B2, then (re)build the FAISS index. This is
the "run indexing" step that makes a document searchable (status → `indexed`).

## Used By
- UI: `/documents/[id]` — the "Run indexing" / "Re-index" button
- API: `POST /documents/{doc_id}/index`

## Core Functions
- `services/api/app/repo/colpali.py` — `embed_images()`, `embed_query()`, `select_device()`
- `services/api/app/service/ingest.py` — `run_indexing()`, `rebuild_index()`
- `services/api/app/repo/faiss_index.py` — `build_index()` (see [FAISS Index](faiss-index.md))
- `services/api/app/repo/store.py` — `.npy` (de)serialization to/from B2

## Model
- Library: `colpali-engine`. Default model `vidore/colpali-v1.2` (base
  `google/paligemma-3b-mix-448`, HF-gated); ungated/lighter alternative
  `vidore/colqwen2-v1.0` (base Qwen2-VL-2B). Chosen per document at ingest.
- Runs **locally** — no external provider key. `HF_TOKEN` is an optional
  one-time model-download token for the gated PaliGemma base, not a per-request
  key; colqwen2 needs no token.
- Cost for a full demo run: **$0**.

## Device Selection
- Runtime autodetect in `select_device()`: `COLPALI_DEVICE` override, else CUDA,
  else CPU. CPU is the default — a GPU is never hard-required.
- Apple MPS is intentionally skipped in autodetect because PaliGemma/ColPali
  float ops are unstable on MPS. Force it with `COLPALI_DEVICE=mps` if you want.

## Inputs
- doc_id: string (path param)
- page images: read from `pages/<id>/<n>.png` in B2

## Outputs
- `embeddings/<id>/<n>.npy` — one multi-vector array per page (float32, L2-normalized)
- Rebuilt `index/index.faiss` + `index/mapping.json`
- Updated `meta.json` (status `indexing` → `indexed`, `pages_indexed`, `embedding_bytes`)

## Status Lifecycle & Progress
- `run_indexing()` flushes `status="indexing"` + `pages_indexed=0` to
  `meta.json` **before** the multi-minute embed begins, then bumps
  `pages_indexed` after each page's `.npy` is written, then sets `indexed` at
  the end. Pages are embedded one at a time so the counter advances
  determinately rather than only at the end.
- The detail page (`useDocument`) **polls** every 2s while `status === "indexing"`
  and renders an advancing progress bar ("Embedding page X of N"). Because the
  in-progress status is persisted, a mid-index reload observes the in-progress
  state (disabled Run-indexing button) and auto-updates to `indexed` when the
  server finishes — no manual reload.
- The POST itself stays synchronous; the persisted status + client polling are
  what make progress observable, not a background-task refactor.

## Flow
- User clicks "Run indexing" on the document detail page (status → `indexing`,
  flushed to B2 before embedding starts)
- API loads each page PNG from B2 and calls `embed_images()` per page, saving the
  multi-vectors as `.npy` under `embeddings/<id>/` and bumping `pages_indexed`
- `rebuild_index()` reloads all embeddings across the corpus and rebuilds the
  global FAISS index, uploading it to `index/`
- Status becomes `indexed`

## Edge Cases
- Document has no rendered pages → 400
- Weights not yet cached → first run downloads them once (multi-GB); use a tiny
  corpus for demos
- Re-index overwrites embeddings and rebuilds the index deterministically

## Verification
- Test files: `services/api/tests/test_ingest.py` (model mocked), `services/api/tests/test_faiss_index.py` (real FAISS math)
- Focused verify command: `pnpm test:api`
- Pass criteria: focused tests and `pnpm verify` green; real embedding is exercised by end-to-end verify with a tiny PDF

## Related Docs
- [FAISS Index](faiss-index.md)
- [Visual Search](visual-search.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
