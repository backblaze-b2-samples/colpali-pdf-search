<!-- last_verified: 2026-07-29 -->
# Feature: Visual Search

## Purpose
The headline capability: type a natural-language query and land on the exact
page of the corpus, retrieved by ColPali vision embeddings over rendered page
images — no OCR, no text extraction.

## Used By
- UI: `/search` page, `VisualSearch` component
- API: `GET /search?q=...&top_k=...`

## Core Functions
- `apps/web/src/components/search/visual-search.tsx` — query box + results grid
- `apps/web/src/lib/queries.ts` — `useVisualSearch()`
- `services/api/app/runtime/search.py` — `GET /search` handler
- `services/api/app/service/search.py` — `search()` orchestration
- `services/api/app/repo/colpali.py` — `embed_query()`
- `services/api/app/repo/faiss_index.py` — `search()` (MaxSim)

## Inputs
- q: string (natural-language query, required, min length 1)
- top_k: int (1–50, default 10)

## Outputs
- `SearchResponse` — `query`, `top_k`, and `hits[]` of `{doc_id, title, page,
  score, key, url}` where `url` is a presigned link to the page image in B2

## Flow
- User submits a query on `/search`
- API reads `index/index.faiss` + `index/mapping.json` from B2
- `embed_query()` produces the query multi-vector with ColPali's query encoder
- `faiss_index.search()` MaxSim-ranks pages; the top pages are returned with
  presigned URLs so the full-resolution images stream straight from B2
- Results render as page thumbnails with relevance scores; clicking opens the
  document detail

## Edge Cases
- Empty query → 422 (route validation)
- No corpus indexed yet → 200 with an empty `hits` list (not an error)
- Nothing matches → empty results state in the UI

## UX States
- Idle: prompt to describe the page you want
- Loading: skeleton grid
- Empty: "No matching pages" (nothing indexed / no match)
- Error: inline error with retry
- Loaded: ranked page thumbnails with scores

## Verification
- Test files: `services/api/tests/test_search.py`, `services/api/tests/test_routes.py`
- Required cases: empty query rejected, empty corpus returns `[]`, ranked hits with titles
- Focused verify command: `pnpm test:api`
- Pass criteria: focused tests and `pnpm verify` green; real retrieval is exercised end-to-end by verify

## Related Docs
- [ColPali Embedding](colpali-embedding.md)
- [FAISS Index](faiss-index.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
