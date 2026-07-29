<!-- last_verified: 2026-07-29 -->
# Feature: Document Library

## Purpose
A scoped explorer for the app's own corpus: browse ingested documents (page
count, status, page-1 thumbnail) scoped to the `documents/` prefix, and open a
document to read, rename, re-index, or delete it. Complements — does not replace
— the full-bucket [File Browser](file-browser.md).

## Used By
- UI: `/library` (grid), `/documents/[id]` (detail)
- API: `GET /documents`, `GET /documents/{doc_id}`, `PATCH /documents/{doc_id}`,
  `DELETE /documents/{doc_id}`, `POST /documents/{doc_id}/index`

## Core Functions
- `apps/web/src/components/library/document-library.tsx` — card grid
- `apps/web/src/components/documents/document-detail.tsx` — detail, rename dialog, delete, run-index, page gallery
- `apps/web/src/lib/queries.ts` — `useDocuments()`, `useDocument()`, `useRenameDocument()`, `useDeleteDocument()`, `useIndexDocument()`
- `services/api/app/runtime/documents.py` — document routes
- `services/api/app/service/documents.py` — CRUD over `documents/<id>/meta.json`

## Primary-entity lifecycle
| Verb | UI | Effect |
|------|----|--------|
| create | `/ingest` | render PDF → store pages + meta (`rendered`) |
| read | `/library`, `/documents/[id]`, dashboard | list; detail with page gallery |
| edit | rename dialog on detail | rename the title in `meta.json` |
| delete | detail / library | prefix-scoped purge + index rebuild |
| run | "Run indexing" on detail | embed pages → `.npy` → (re)build FAISS → `indexed` |

## Inputs / Outputs
- List → `Document[]` (each with a presigned page-1 `thumbnail_url`)
- Detail → `DocumentDetail` (summary + presigned URLs for every page)
- Rename → updated `Document`
- Delete → `{ deleted: true, id }`; removes `pages/<id>/`, `embeddings/<id>/`,
  `documents/<id>/` (scoped — never a bucket-wide wipe) and rebuilds the index

## Edge Cases
- Invalid document id → 400
- Missing document → 404
- Empty corpus → empty state with a link to Ingest

## UX States
- Loading: skeleton cards
- Empty: "No documents yet"
- Error: inline error with retry
- Loaded: thumbnail cards with status badge; detail with page gallery

## Verification
- Test files: `services/api/tests/test_documents.py`, `services/api/tests/test_routes.py`
- Focused verify command: `pnpm test:api`
- Pass criteria: focused tests and `pnpm verify` green

## Related Docs
- [Document Ingest](document-ingest.md)
- [File Browser](file-browser.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
