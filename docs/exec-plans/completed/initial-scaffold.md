# Build plan — `colpali-pdf-search`

Source of truth for the starter tree:
`.claude/scratch/vcsk-9f722f25-fa1a-4776-a2ed-d2e79f25077f/` (fresh clone, Phase 0).
Build target: `./colpali-pdf-search`.

## 1. Purpose

`colpali-pdf-search` is a self-hosted **visual document search** app: it retrieves
the right *page* of a PDF corpus using vision embeddings (ColPali) over rendered
page images — **no OCR, no text extraction**. An analyst types a natural-language
query ("show me the slide with the revenue waterfall chart") and lands on the exact
page. It is for enterprise knowledge-management teams and research orgs that must
search across thousands of reports, decks, and scanned documents.

Its B2 story is **write amplification**: one PDF explodes into many page PNGs plus
per-page multi-vector embedding files (which can equal or exceed the raw image
footprint) plus a FAISS index — all stored in and streamed from Backblaze B2 over
the S3-compatible API. B2 is the single storage layer; the only credentials are
`B2_*` (the ColPali model runs locally, no second provider key).

## 2. Architecture delta from vibe-coding-starter-kit

The starter kit is the ceiling — keep its full-stack shell (Next.js 16 + React 19 +
Tailwind v4 + shadcn/ui web, FastAPI layered backend `types→config→repo→service→
runtime`, structural tests, agent docs) and strip/extend rather than rebuild.

### KEEP (as-is or lightly rebranded)
- Web shell: `apps/web` app-router layout, sidebar, header, theme provider,
  command palette, health banner, `components/ui/*` (shadcn), design tokens,
  `/design` design-system page.
- **Bucket explorer (`/files` page + `files` API routes) — NON-NEGOTIABLE KEEP.**
  Full-bucket browse with preview/download/delete stays exactly as shipped. It is
  never removed. (See the mandatory add of a scoped Library below — they coexist.)
- FastAPI shell: `main.py` app/middleware/logging, `repo/b2_client.py` S3 client
  (adapted for env-var rename + new ops), `runtime/health.py`, `runtime/metrics.py`,
  `runtime/ratelimit.py`, layered structure + `tests/test_structure.py` invariants.
- Settings form pattern (`components/settings/settings-form.tsx`) as the exemplar
  for the new create/edit forms; keep `/settings` + `danger-zone.tsx`.
- Tooling: pnpm workspace, ruff/ESLint, pytest, playwright, `scripts/*`, pre-commit.

### TRIM (remove or repurpose from starter)
- Generic "file upload" framing → repurposed into **document ingest** (see add).
- `docs/features/metadata-extraction.md` (image EXIF/metadata extraction) →
  delete; replaced by embedding docs.
- Starter README screenshots/copy → fully rewritten (no binary assets added here;
  screenshots are a later pipeline step).
- Any "OSS Starter Kit"/"Vibe Coding Starter Kit" branding strings → renamed
  (see rename table §6).

### ADD (new for colpali-pdf-search)
- **repo/ layer (external SDKs contained here, per structural invariant):**
  - `repo/pdf_render.py` — PDF → per-page PNG renders using **PyMuPDF (`fitz`)**
    (pip-only, no system poppler dependency). dpi-configurable.
  - `repo/colpali.py` — ColPali model wrapper: lazy-load model + processor,
    device autodetect, `embed_images(list[PIL.Image]) -> multi-vectors` and
    `embed_query(text) -> multi-vectors`.
  - `repo/faiss_index.py` — build an `IndexFlatIP` over all page patch vectors +
    a `mapping.json` (row → doc_id/page/patch), MaxSim late-interaction search,
    (de)serialize index+mapping to/from bytes for B2.
  - Extend `repo/b2_client.py` with the new object ops (get/stream bytes,
    prefixed listing, JSON meta read/write, prefix-scoped delete).
- **service/ layer (orchestration, no SDK imports):**
  - `service/documents.py` — document CRUD over B2 `documents/<id>/meta.json`.
  - `service/ingest.py` — render → store pages; embed → store `.npy`; build index.
  - `service/search.py` — query embed → index search → ranked pages.
- **runtime/ layer (routes):** `runtime/documents.py`, `runtime/search.py`.
- **Web pages:** `/ingest` (create), `/library` (scoped asset explorer),
  `/documents/[id]` (read/detail + edit/delete/run controls), `/search`
  (headline query UI). Nav (`app-sidebar.tsx`), header `pageTitles`, and
  command palette updated for the new routes.
- **Sample-specific asset explorer — MANDATORY ADD:** `/library` — a "Document
  Library" view scoped to the app's own `documents/` prefix (ingested docs with
  page-count, status, thumbnail of page 1). This is the sample-scoped explorer
  that complements (does not replace) the full-bucket `/files` explorer.

*Note (bucket-explorer tension):* a pure search app arguably doesn't need a raw
full-bucket browser, but per skill rule the bucket explorer stays; it doubles here
as a useful "see the raw pages/embeddings/index objects B2 is holding" view that
reinforces the write-amplification story. Kept intentionally.

## 3. B2 surface (S3-compatible only — no b2-native)

All access via boto3 S3 client in `repo/` (containment invariant). Object layout:
- `pages/<doc-id>/<n>.png` — rendered page images (`put_object`, streamed via
  `get_object`/presigned to UI).
- `embeddings/<doc-id>/<n>.npy` — per-page multi-vector ColPali embeddings
  (`put_object`; `get_object` when (re)building the index).
- `index/index.faiss` + `index/mapping.json` — the FAISS index + row→page map
  (`put_object` on build; `get_object` on search).
- `documents/<doc-id>/meta.json` — small document record (title, page_count,
  dpi, model, status, timestamps).

S3 operations exercised: `put_object`, `get_object`, `list_objects_v2` (paginated,
both full-bucket and `documents/`-scoped), `head_object`, `head_bucket` (health),
`delete_object` (prefix-scoped purge), `generate_presigned_url` (serve page PNGs).
**No b2-native API anywhere** — default per parent CLAUDE.md #1 is satisfied.

Deletes are scoped to the specific document's prefixes (`pages/<id>/`,
`embeddings/<id>/`, `documents/<id>/`) — never a bucket-wide wipe (CLAUDE.local
safety rule). Index is rebuilt from remaining embeddings after a delete.

## 4. Key features

1. **Document ingest (create)** — upload a PDF, render pages to PNG at a chosen
   dpi, store under `pages/<id>/`, write `meta.json` (status `rendered`).
2. **ColPali embedding + FAISS index (run)** — embed each page image into a
   multi-vector late-interaction embedding, store `.npy` under `embeddings/<id>/`,
   (re)build the FAISS index and `mapping.json`, upload to `index/`; status
   `indexed`. Triggerable per document ("Run indexing").
3. **Visual search (query — headline)** — embed a text query with ColPali's query
   encoder, MaxSim-retrieve nearest pages from the FAISS index, stream the
   full-resolution page images from B2 with per-page relevance scores.
4. **Document library (scoped explorer)** — browse ingested documents (page count,
   status, page-1 thumbnail) scoped to the `documents/` prefix; open detail;
   rename/delete/re-index from there.
5. **Full-bucket explorer (kept)** — the starter's `/files` browse over every raw
   object (pages, embeddings, index) with preview/download/delete.
6. **Dashboard** — corpus stats: documents indexed, total pages, page-image bytes
   vs embedding bytes (the write-amplification headline), index size.

### External API provider
- **ColPali page/query embedding** — `deployment: **local**`.
  - Rationale: a specific on-device model/framework (ColPali) IS the sample's whole
    point → api-provider-selection Step 2 rule 1 makes LOCAL the default.
  - Provider/model: **no external provider**. Library `colpali-engine`; default
    model `vidore/colpali-v1.2` (base `google/paligemma-3b-mix-448`), configurable
    via `COLPALI_MODEL`. Lighter ungated alternative documented:
    `vidore/colqwen2-v1.0` (base Qwen2-VL-2B, no gate).
  - Cost for one full demo run: **$0** (runs locally).
  - Env var for key: **none** (B2 credentials only). The default model's base is
    HF-gated, so a *one-time* free Hugging Face account + accepting PaliGemma terms
    is needed to download weights; expose an **optional** `HF_TOKEN` env var
    (placeholder in `.env.example`, documented like a model-download token — NOT a
    per-run provider key). The ungated `colqwen2` alternative needs no token.
  - Device: **CPU default, autodetect CUDA → MPS → CPU** (hard rule). MPS support
    for PaliGemma float ops is weak/flaky → allow `COLPALI_DEVICE` override and, on
    MPS instability, fall back CUDA → CPU. Note: weights are multi-GB, downloaded
    once and cached; a demo run should use a tiny corpus (1–2 short PDFs, few pages).
- No other feature needs an external API.

### Provider orchestration via Genblaze
- **Not applicable.** The description does not mention Genblaze / `genblaze-*` /
  `genblaze-s3`. Do NOT introduce the Genblaze SDK. ColPali is called directly via
  `colpali-engine` inside `repo/colpali.py`.

### Primary-entity lifecycle (UI completeness)
Primary entity: **Document** (one ingested PDF). The app genuinely splits ingest
into render (create) and embed+index (run), so every verb is real, not hypothetical:

| Verb | UI | What it does |
|------|----|--------------|
| **create** | `/ingest` form | upload PDF → render pages → store PNGs + meta (status `rendered`) |
| **read** | `/library`, `/documents/[id]`, dashboard | list docs; detail with page gallery (streamed from B2), status, counts |
| **edit** | rename dialog on detail | rename the document title in `meta.json` |
| **delete** | detail / library action | prefix-scoped purge of the doc's pages/embeddings/meta + index rebuild |
| **run** | "Run indexing" button on detail | embed pages → store `.npy` → (re)build FAISS index → status `indexed` |

All five verbs are built → `omitted_ui_verbs` is expected to be **empty**.
(Corpus-level **Visual Search** is a top-level headline capability, not a CRUD verb
on a single Document; it lives at `/search`.)

### Form UX conventions
- **Create form (`/ingest`)** — fields:
  - PDF file (upload; required).
  - Title (free text — no finite set → plain input). Placeholder/FormDescription
    default hint, e.g. "Q3 Financial Report" (guidance only, no autofill button).
  - dpi — **finite set → `Select`** (72 / 100 / 150), default 150 surfaced via
    FormDescription ("150 dpi — sharp thumbnails; lower = smaller/faster").
  - model — **finite set → `Select`** (`vidore/colpali-v1.2`,
    `vidore/colqwen2-v1.0`), default `vidore/colpali-v1.2` with a note that
    colqwen2 is ungated/lighter.
- **Edit form (rename dialog)** — Title only, pre-filled from the real doc (no
  default hint; it opens on real data). No finite-set fields, so no selector.
- Mirror the starter's `settings-form.tsx` (react-hook-form + zod + shadcn `Form`,
  `Select`, `FormDescription`) — it already does both conventions.

## 5. Doc transforms
- `README.md` → full rewrite for ColPali visual PDF search (features list from §4,
  quickstart with the renamed `B2_*` vars, the write-amplification "why B2" angle).
- `docs/features/file-upload.md` → rewrite as `docs/features/document-ingest.md`.
- `docs/features/metadata-extraction.md` → **delete**; replace with
  `docs/features/colpali-embedding.md`.
- `docs/features/file-browser.md` → **keep** (bucket explorer) + add
  `docs/features/document-library.md` (scoped explorer).
- `docs/features/dashboard.md` → rewrite for corpus/index stats.
- **Add:** `docs/features/visual-search.md`, `docs/features/faiss-index.md`.
- `ARCHITECTURE.md` → add the ingest→embed→index→query data flow and the new
  repo/service/runtime modules; keep layering invariants.
- `AGENTS.md` → update repo layout, env-var names, and commands.
- Each new feature gets a `docs/features/<feature>.md` from `_template.md`.

## 6. Rename table

| From (starter) | To (`colpali-pdf-search`) |
|---|---|
| `vibe-coding-starter-kit` (kebab / dir / repo) | `colpali-pdf-search` |
| `@vibe-coding-starter-kit/web` (pnpm pkg) | `@colpali-pdf-search/web` |
| "Vibe Coding Starter Kit" / "OSS Starter Kit" (Title Case, `APP_NAME`, README, API title) | "ColPali PDF Search" |
| `user_agent_extra="b2ai-oss-start"` | `user_agent_extra="b2ai-colpali-pdf-search"` |
| `utm_content=b2ai-oss-start` (README B2 links) | `utm_content=b2ai-colpali-pdf-search` |
| docker image / compose tags, `.github` workflow names referencing the starter | `colpali-pdf-search` |
| `APP_NAME` const in `apps/web/src/lib/app-config.ts` | `"ColPali PDF Search"` |

### Env-var rename — STANDARD #3 COMPLIANCE (must-do, b2-doctor + reviewer gate this)
The starter uses non-standard names. Rename everywhere they appear
(`config/settings.py`, `repo/b2_client.py`, `main.py` `REQUIRED_B2_SETTINGS` +
`PLACEHOLDER_VALUES`, `.env.example`, README, docs, AGENTS.md):

| Starter | Standard (target) |
|---|---|
| `B2_KEY_ID` | `B2_APPLICATION_KEY_ID` |
| `B2_APPLICATION_KEY` | `B2_APPLICATION_KEY` (unchanged) |
| `B2_BUCKET_NAME` | `B2_BUCKET_NAME` (unchanged) |
| `B2_ENDPOINT` | `B2_REGION` (derive `endpoint_url=https://s3.{region}.backblazeb2.com`; also pass `region_name`) |
| `B2_PUBLIC_URL` | `B2_PUBLIC_URL_BASE` |

`.env.example` must list exactly: `B2_APPLICATION_KEY_ID`, `B2_APPLICATION_KEY`,
`B2_BUCKET_NAME`, `B2_REGION`, `B2_PUBLIC_URL_BASE` (+ optional `HF_TOKEN`,
`COLPALI_MODEL`, `COLPALI_DEVICE`). No real secrets — placeholders only.

## 7. Dependencies (pin — unpinned ML reqs are a false-green trap)
Add to `services/api` requirements (bounded ranges, not unbounded):
`colpali-engine`, `torch`, `torchvision`, `transformers`, `pillow`, `pymupdf`
(PDF render — no poppler), `faiss-cpu`, `numpy<2`, `einops`. Keep existing
`boto3`, `fastapi`, `pydantic-settings`, `python-dotenv`. Verify `faiss-cpu` +
`torch` + `numpy<2` resolve together on arm64. External SDKs (torch, colpali,
faiss, fitz) import **only** in `repo/` so `tests/test_structure.py` passes — extend
that test's allowed-SDK list if it hard-codes `boto3` as the sole repo SDK.

## 8. Build guardrails
- Keep every file ≤ 300 lines (enforced). Split model/index/render into the
  separate repo modules above.
- `pnpm lint`, `pnpm build`, `pnpm test:api`, `pnpm check:structure` must pass at
  the end of the build (the timed-out-build trap leaves docs/lint undone — confirm
  these explicitly).
- Do NOT run the ColPali model or download multi-GB weights during build; scaffold
  and unit-test with the model layer mocked/skipped. Real inference is verify's job.
- No screenshots, no remote push, no touching sibling samples.
