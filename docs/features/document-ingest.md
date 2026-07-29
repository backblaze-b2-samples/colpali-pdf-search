<!-- last_verified: 2026-07-29 -->
# Feature: Document Ingest

## Purpose
Turn an uploaded PDF into a searchable document by rendering every page to an
image and storing those images in Backblaze B2 (status `rendered`). Embedding +
indexing is a separate step — see [ColPali Embedding](colpali-embedding.md).

## Used By
- UI: `/ingest` page, `IngestForm` component
- API: `POST /documents` (multipart)

## Core Functions
- `apps/web/src/components/ingest/ingest-form.tsx` — file picker + title/dpi/model form
- `apps/web/src/lib/api-client.ts` — `ingestDocument()` (XHR, progress events)
- `services/api/app/runtime/documents.py` — `POST /documents` handler
- `services/api/app/service/ingest.py` — `create_document()` orchestration
- `services/api/app/repo/pdf_render.py` — `render_pdf_to_pngs()` via PyMuPDF (fitz)
- `services/api/app/repo/store.py` — `put_bytes()` / `write_json()` to B2

## Inputs
- file: PDF (multipart, required, max 100 MB)
- title: string (free text; defaults to "Untitled document")
- dpi: 72 | 100 | 150 (finite `Select`, default 150)
- model: `vidore/colpali-v1.2` | `vidore/colqwen2-v1.0` (finite `Select`)

## Outputs
- `Document` record (id, title, page_count, dpi, model, status=`rendered`, byte counts)
- Side effects in B2: `pages/<id>/<n>.png` for every page, `documents/<id>/meta.json`

## Flow
- User picks a PDF, sets a title, dpi, and model on `/ingest`
- Client streams the PDF to `POST /documents` with a progress bar
- API validates dpi/model against the finite allow-lists and the leading bytes (`%PDF-`)
- `render_pdf_to_pngs()` rasterizes each page at the chosen dpi (no OCR, no poppler)
- Each page PNG is stored at `pages/<id>/<n>.png`; a `meta.json` records the document
- API returns the `Document`; the UI redirects to `/documents/<id>`

## Edge Cases
- Non-PDF bytes → 415 "not a valid PDF"
- PDF too large (>100 MB) → 413
- Unsupported dpi or model → 400
- PDF with no renderable pages → 400

## UX States
- Empty: file picker prompt
- Loading: upload/render progress bar
- Error: toast with the API message
- Complete: toast + redirect to the document detail page

## Verification
- Test files: `services/api/tests/test_ingest.py`, `services/api/tests/test_pdf_render.py`, `services/api/tests/test_routes.py`
- Required cases: render + store happy path, non-PDF rejection, bad dpi/model rejection
- Focused verify command: `pnpm test:api`
- Default pre-PR verify command: `pnpm verify`
- Full local verify command: `pnpm verify:full` when the E2E/live prerequisites apply
- Pass criteria: focused tests and `pnpm verify` green

## Related Docs
- [ColPali Embedding](colpali-embedding.md)
- [Document Library](document-library.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
