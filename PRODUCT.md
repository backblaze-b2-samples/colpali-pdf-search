# Product

## Register

product

## Users

Enterprise knowledge-management teams and research orgs that must search across
thousands of reports, decks, and scanned documents — where the answer is a
*page* (a chart, a diagram, a slide), not a paragraph of extractable text. Their
context: OCR pipelines miss layout, figures, and scans; they want to type what
they remember and land on the exact page. Analysts run the searches; a developer
self-hosts the app against their own Backblaze B2 bucket.

## Product Purpose

ColPali PDF Search is a self-hosted visual document search app. It renders every
PDF page to an image, embeds each page with ColPali vision embeddings (running
locally), indexes them with FAISS, and answers natural-language queries by
returning the matching pages — no OCR, no text extraction. Every artifact (page
images, per-page embeddings, the FAISS index) is stored in and streamed from
Backblaze B2 over the S3-compatible API; B2 is the single storage layer.
Success = ingest a corpus, run indexing, type a query, and land on the right
page with a relevance score.

## Brand Personality

Confident, precise, quietly professional. Voice is direct and free of hype. The
interface should feel like a modern developer/analyst tool — considered, calm,
trustworthy — that makes a storage-heavy AI workload feel legible: you can see
the pages, the embeddings, and the index that B2 is holding.

## Anti-references

- **Generic AI/SaaS slop.** No gradient text, hero-metric templates, identical
  icon-card grids, tracked uppercase eyebrows, or decorative glassmorphism. These are
  the exact 2026 AI tells this kit exists to help builders avoid.
- **Over-branded / loud.** No heavy brand-color drenching, decorative motion, or flashy
  effects. It is scaffolding to be rebranded, not a hero page.
- **Toy / prototype feel.** No missing states, inconsistent components, or placeholder
  polish. Must read as production-grade.
- **Enterprise-drab.** No Bootstrap-era gray boxes or dense-but-lifeless admin-panel
  look. Considered, like modern dev tools (Linear, GitHub Primer, Stripe).

## Design Principles

- **Practice what you preach.** The kit itself must model the production quality it
  asks agents to produce. Slop here propagates into every project built on it.
- **Neutral foundation, easy to rebrand.** Identity lives in tokens (`globals.css`) and
  one config file. Screens are built from the shared UI kit so a rebrand is a token
  swap, not a rewrite.
- **Earned familiarity over novelty.** Use standard, trusted affordances (top bar +
  side nav, command palette, data tables). The tool disappears into the task.
- **Every state is designed.** Default, hover, focus, active, disabled, loading (skeleton),
  empty (teaches the interface), and error (says what's wrong + offers retry) — never
  half-shipped.
- **Consistency is the feature.** One button vocabulary, one form-control set, one icon
  style across every screen. Divergence is a bug.

## Accessibility & Inclusion

Target **WCAG 2.1 AA**. Body text ≥ 4.5:1, large/bold text ≥ 3:1, visible focus
indicators on every interactive element, full keyboard navigation, correct semantic
landmarks and heading order, labelled form controls, and a `prefers-reduced-motion`
alternative for every animation. Full light and dark theme parity.
