# Tech debt

Backlog of nitpick-severity observations surfaced during verification. These do
not block the main feature; they are "could be nicer" items, not defects.

## 2026-07-29 — verify

- /ingest + /search (first run, default model) — the default model `vidore/colpali-v1.2` (PaliGemma base, ~6GB) downloads once on the first index and first search; the in-progress copy never says a *download* is happening (the new per-page embed progress only covers the embed phase). On a fresh clone the first two core actions look stalled for ~6 min. → Add a distinct "Downloading model weights (one-time, ~6GB)…" state, and/or default to the lighter ungated `vidore/colqwen2-v1.0`. (.local/verify/A/12-indexing-inprogress.png)
- Sidebar (all pages) — "Ingest" (corpus ingest) sits beside "Upload" and "Files" (the starter's generic B2 file browser/upload). → A first-time user aiming to add a searchable PDF could click "Upload" instead of "Ingest"; consider visually separating corpus actions from the raw file browser. (.local/verify/A/01-dashboard.png)
- /search results grid — result page thumbnails render faint/near-blank on white cards (ColPali paper pages are light text-on-white with no backdrop/border behind the image). → Images are real (naturalWidth 1275, legible at detail size) but look almost empty at thumbnail scale; add a subtle backdrop/border or checkerboard behind page thumbnails. (.local/verify/C/40-q-tables.png)
- Document delete — a benign `404 Not Found` console error fires immediately after delete (a post-delete refetch of the now-removed document races the redirect). → UI redirects cleanly to /library with a success toast; cancel/skip the refetch on delete to silence the console error. (.local/verify/C/51-delete-dialog.png)
- /search → result click — clicking a search result navigates to `/documents/{id}` (the whole document) rather than deep-linking or scrolling to the exact matched page. → The matched page number, score, and that page's image are already surfaced on the result card, so the goal is met at the result level; a deep-link/scroll-to-page would close the loop. (.local/verify/RV1/13-result-landing.png)
