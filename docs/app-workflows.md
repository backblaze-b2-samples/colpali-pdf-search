<!-- last_verified: 2026-07-29 -->
# App Workflows

User journeys inside ColPali PDF Search.

## Ingest a Document

- User navigates to `/ingest`
- Chooses a PDF, sets a title, picks a render resolution (72/100/150 dpi) and a
  ColPali model
- Client streams the PDF to `POST /documents` with a progress bar
- API renders each page to a PNG and stores them in B2 under `pages/<id>/`
- On success: toast, redirect to the document detail page (status `rendered`)
- See: [Document Ingest](features/document-ingest.md)

## Index a Document (make it searchable)

- On `/documents/[id]`, user clicks "Run indexing"
- API embeds every page image with ColPali, stores per-page `.npy` vectors in
  B2, and (re)builds the FAISS index in `index/`
- Status becomes `indexed`; embeddings byte count appears in the stats row
- See: [ColPali Embedding](features/colpali-embedding.md), [FAISS Index](features/faiss-index.md)

## Search Visually

- User navigates to `/search`
- Types a natural-language query ("the slide with the revenue waterfall chart")
- API embeds the query, MaxSim-ranks pages against the FAISS index, and returns
  the matching page images (streamed from B2) with relevance scores
- Clicking a result opens the source document
- Empty corpus → an empty results state, not an error
- See: [Visual Search](features/visual-search.md)

## Browse the Library

- User navigates to `/library`
- Sees a grid of ingested documents scoped to the `documents/` prefix, each with
  a page-1 thumbnail, status badge, page count, dpi, and model
- Opening a document shows the page gallery and rename / re-index / delete actions
- Rename edits the title in `meta.json`; delete purges the document's pages,
  embeddings, and meta (scoped) and rebuilds the index
- See: [Document Library](features/document-library.md)

## View the Dashboard

- User navigates to `/` (home)
- Stat cards: documents, indexed, total pages, index size
- Storage panel contrasts page-image bytes vs embedding bytes (write
  amplification) with the embedding:image ratio
- See: [Dashboard](features/dashboard.md)

## Browse the Raw Bucket (starter explorer, kept)

- User navigates to `/files`
- Full-bucket tree view of every raw object — page PNGs, `.npy` embeddings, the
  FAISS index, `meta.json` — with preview, download, and delete
- A useful "see what B2 is actually holding" view that reinforces the
  write-amplification story
- Generic upload remains at `/upload`
- See: [File Browser](features/file-browser.md)
