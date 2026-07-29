<!-- last_verified: 2026-07-29 -->
# Feature: Dashboard

## Purpose
Give an at-a-glance overview of the visual-search corpus and its storage
footprint in B2 — including the write-amplification headline (page-image bytes
vs embedding bytes).

## Used By
- UI: `/` page (dashboard home)
- API: `GET /documents/stats`

## Core Functions
- `apps/web/src/components/dashboard/corpus-stats.tsx` — stat cards + storage panel
- `apps/web/src/lib/queries.ts` — `useCorpusStats()`
- `services/api/app/runtime/documents.py` — `GET /documents/stats` handler
- `services/api/app/service/documents.py` — `corpus_stats()` aggregation

## Inputs
- None (loads automatically)

## Outputs
- `GET /documents/stats` → `CorpusStats`: documents, indexed_documents,
  total_pages, page_bytes(+human), embedding_bytes(+human), index_bytes(+human)

## Flow
- Page loads → one API call for corpus stats
- Four cards: Documents, Indexed, Total Pages, Index Size
- A storage panel contrasts page-image bytes vs embedding bytes and shows the
  embedding:image ratio — the write-amplification story that motivates B2 as the
  single storage layer
- Quick actions link to Ingest and Visual Search

## Edge Cases
- API unavailable → inline error state with retry
- Empty corpus → zeros / "0 B"
- Large corpus → stats paginate through the `documents/` and `index/` prefixes

## UX States
- Loading: skeleton stat values
- Empty: zeros
- Loaded: populated cards + storage panel

## Verification
- Test files: `services/api/tests/test_documents.py` (`test_corpus_stats`)
- Focused verify command: `pnpm test:api`
- Pass criteria: focused tests and `pnpm verify` green

## Related Docs
- [Document Library](document-library.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
