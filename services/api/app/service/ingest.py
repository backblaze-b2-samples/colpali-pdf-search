"""Ingest pipeline: render a PDF to page images (create), then embed those
pages with ColPali and (re)build the corpus FAISS index (run).

The two verbs are deliberately separate: rendering is cheap and immediate,
embedding loads a multi-GB model and is triggered per document from the UI.
"""

import io
import logging
from datetime import UTC, datetime

import numpy as np

from app.config import settings
from app.repo import colpali, store
from app.repo.faiss_index import PageVectors, build_index
from app.repo.pdf_render import render_pdf_to_pngs
from app.service.documents import (
    DOCS_PREFIX,
    EMBED_PREFIX,
    INDEX_KEY,
    MAPPING_KEY,
    PAGES_PREFIX,
    DocumentNotFound,
    load_meta,
    new_document_id,
    save_meta,
    validate_doc_id,
)
from app.types import Document

logger = logging.getLogger(__name__)


class IngestError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _npy_bytes(arr: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, arr)
    return buffer.getvalue()


def _load_npy(data: bytes) -> np.ndarray:
    return np.load(io.BytesIO(data))


def _page_number(key: str) -> int:
    stem = key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return int(stem) if stem.isdigit() else 0


def create_document(
    pdf_bytes: bytes, title: str, dpi: int, model: str
) -> Document:
    """Render a PDF to page PNGs in B2 and write its meta (status=rendered)."""
    if pdf_bytes[:5] != b"%PDF-":
        raise IngestError("Uploaded file is not a valid PDF", status_code=415)

    try:
        pages = render_pdf_to_pngs(pdf_bytes, dpi=dpi)
    except RuntimeError as e:
        raise IngestError(str(e), status_code=400) from e

    doc_id = new_document_id()
    page_bytes = 0
    for number, png in enumerate(pages, start=1):
        page_bytes += store.put_bytes(
            f"{PAGES_PREFIX}{doc_id}/{number}.png", png, "image/png"
        )

    now = datetime.now(UTC).isoformat()
    meta = {
        "id": doc_id,
        "title": title.strip() or "Untitled document",
        "page_count": len(pages),
        "dpi": dpi,
        "model": model,
        "status": "rendered",
        "created_at": now,
        "updated_at": now,
        "page_bytes": page_bytes,
        "embedding_bytes": 0,
    }
    save_meta(meta)
    logger.info("Document ingested: id=%s pages=%d", doc_id, len(pages))
    return Document(**meta)


def run_indexing(doc_id: str) -> Document:
    """Embed a document's pages with ColPali, store the vectors, and rebuild
    the corpus index. Status becomes `indexed`."""
    validate_doc_id(doc_id)
    meta = load_meta(doc_id)
    if not meta:
        raise DocumentNotFound(doc_id)

    page_objs = store.list_prefix(f"{PAGES_PREFIX}{doc_id}/")
    page_objs.sort(key=lambda obj: _page_number(obj["Key"]))
    if not page_objs:
        raise IngestError("Document has no rendered pages to index")

    images = [store.get_object_bytes(obj["Key"]) for obj in page_objs]
    embeddings = colpali.embed_images(images, model_name=meta["model"])

    embedding_bytes = 0
    for obj, vectors in zip(page_objs, embeddings, strict=True):
        number = _page_number(obj["Key"])
        embedding_bytes += store.put_bytes(
            f"{EMBED_PREFIX}{doc_id}/{number}.npy",
            _npy_bytes(vectors),
            "application/octet-stream",
        )

    meta["status"] = "indexed"
    meta["embedding_bytes"] = embedding_bytes
    meta["updated_at"] = datetime.now(UTC).isoformat()
    save_meta(meta)

    rebuild_index()
    logger.info("Document indexed: id=%s pages=%d", doc_id, len(page_objs))
    return Document(**meta)


def rebuild_index() -> None:
    """Rebuild the global FAISS index from every stored embedding and upload it
    to B2 (index/index.faiss + index/mapping.json). Called after indexing a new
    document and after a delete."""
    pages: list[PageVectors] = []
    for doc_obj in store.list_prefix(DOCS_PREFIX):
        if not doc_obj["Key"].endswith("/meta.json"):
            continue
        doc_id = doc_obj["Key"].split("/")[1]
        for emb_obj in store.list_prefix(f"{EMBED_PREFIX}{doc_id}/"):
            vectors = _load_npy(store.get_object_bytes(emb_obj["Key"]))
            pages.append(
                PageVectors(
                    doc_id=doc_id, page=_page_number(emb_obj["Key"]), vectors=vectors
                )
            )

    if not pages:
        # Nothing indexed anymore — drop the stale index so search returns empty.
        store.delete_prefix(INDEX_KEY)
        store.delete_prefix(MAPPING_KEY)
        return

    index_bytes, mapping = build_index(pages)
    store.put_bytes(INDEX_KEY, index_bytes, "application/octet-stream")
    store.write_json(MAPPING_KEY, mapping)


# Finite option sets surfaced in the ingest form (and validated server-side).
ALLOWED_DPI = (72, 100, 150)
ALLOWED_MODELS = ("vidore/colpali-v1.2", "vidore/colqwen2-v1.0")
DEFAULT_MODEL = settings.colpali_model
