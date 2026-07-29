<!-- last_verified: 2026-07-29 -->
# Feature: FAISS Index

## Purpose
Store and search ColPali page embeddings with a FAISS index that lives entirely
in Backblaze B2, using MaxSim late interaction so a multi-vector text query
ranks whole pages.

## Used By
- API: indirectly by `POST /documents/{doc_id}/index` (build) and `GET /search` (query)

## Core Functions
- `services/api/app/repo/faiss_index.py` — `build_index()`, `search()`, `PageVectors`
- `services/api/app/service/ingest.py` — `rebuild_index()` (build + upload to B2)
- `services/api/app/service/search.py` — loads the index from B2 and ranks

## How It Works
- Every page contributes many patch vectors. All patches from all pages are
  flattened into one `IndexFlatIP` (inner product == cosine, because vectors are
  L2-normalized in `repo/colpali.py`).
- A `mapping.json` records `row -> {doc_id, page}` alongside the index.
- **MaxSim scoring**: for each query token, take the best-matching patch per
  page, then sum those maxima across query tokens. This is the ColPali
  late-interaction score, computed here over an approximate-nearest-neighbor
  patch retrieval so it scales as the corpus grows.

## Inputs / Outputs
- Build input: `list[PageVectors]` (doc_id, page, `[num_patches, dim]` array)
- Build output: serialized index bytes + mapping dict → `index/index.faiss`,
  `index/mapping.json` in B2
- Search input: index bytes + mapping + query multi-vector + `top_k`
- Search output: `[(doc_id, page, score), ...]` ranked descending

## Edge Cases
- Empty corpus (no embeddings) → the index objects are deleted; search returns `[]`
- Deleting a document rebuilds the index from the remaining embeddings

## Verification
- Test files: `services/api/tests/test_faiss_index.py` (real FAISS + synthetic vectors)
- Required cases: build + rank aligned page first, empty index, reject no-pages build
- Focused verify command: `pnpm test:api`
- Pass criteria: focused tests and `pnpm verify` green

## Related Docs
- [ColPali Embedding](colpali-embedding.md)
- [Visual Search](visual-search.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
