"""Document CRUD over B2 objects. A "document" is one ingested PDF, recorded at
`documents/<id>/meta.json`; its rendered pages live at `pages/<id>/<n>.png` and
its ColPali embeddings at `embeddings/<id>/<n>.npy`. There is no database — B2
is the sole store.
"""

import logging
import re
import uuid
from datetime import UTC, datetime

from app.repo import store
from app.types import CorpusStats, Document, DocumentDetail, DocumentPage
from app.types.formatting import humanize_bytes

logger = logging.getLogger(__name__)

DOCS_PREFIX = "documents/"
PAGES_PREFIX = "pages/"
EMBED_PREFIX = "embeddings/"
INDEX_PREFIX = "index/"
INDEX_KEY = "index/index.faiss"
MAPPING_KEY = "index/mapping.json"

_DOC_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class DocumentNotFound(Exception):
    def __init__(self, doc_id: str):
        self.detail = f"Document '{doc_id}' not found"
        super().__init__(self.detail)


class InvalidDocumentId(Exception):
    def __init__(self) -> None:
        self.detail = "Invalid document id"
        super().__init__(self.detail)


def new_document_id() -> str:
    return uuid.uuid4().hex


def validate_doc_id(doc_id: str) -> None:
    if not _DOC_ID_RE.match(doc_id):
        raise InvalidDocumentId()


def meta_key(doc_id: str) -> str:
    return f"{DOCS_PREFIX}{doc_id}/meta.json"


def load_meta(doc_id: str) -> dict | None:
    return store.read_json(meta_key(doc_id))


def save_meta(meta: dict) -> None:
    store.write_json(meta_key(meta["id"]), meta)


def _meta_to_document(meta: dict) -> Document:
    document = Document(**meta)
    if document.page_count > 0:
        document.thumbnail_url = store.presign_get(
            f"{PAGES_PREFIX}{document.id}/1.png"
        )
    return document


def list_documents() -> list[Document]:
    """Every ingested document, newest first (scoped to `documents/`)."""
    documents: list[Document] = []
    for obj in store.list_prefix(DOCS_PREFIX):
        if not obj["Key"].endswith("/meta.json"):
            continue
        meta = store.read_json(obj["Key"])
        if meta:
            documents.append(_meta_to_document(meta))
    documents.sort(key=lambda d: d.created_at, reverse=True)
    return documents


def get_document(doc_id: str) -> Document:
    validate_doc_id(doc_id)
    meta = load_meta(doc_id)
    if not meta:
        raise DocumentNotFound(doc_id)
    return _meta_to_document(meta)


def _page_number(key: str) -> int:
    stem = key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return int(stem) if stem.isdigit() else 0


def get_document_detail(doc_id: str) -> DocumentDetail:
    """Document summary plus presigned URLs for every rendered page image."""
    document = get_document(doc_id)
    page_objs = store.list_prefix(f"{PAGES_PREFIX}{doc_id}/")
    page_objs.sort(key=lambda obj: _page_number(obj["Key"]))
    pages = [
        DocumentPage(
            page=_page_number(obj["Key"]),
            key=obj["Key"],
            url=store.presign_get(obj["Key"]),
        )
        for obj in page_objs
    ]
    return DocumentDetail(**document.model_dump(), pages=pages)


def rename_document(doc_id: str, title: str) -> Document:
    validate_doc_id(doc_id)
    meta = load_meta(doc_id)
    if not meta:
        raise DocumentNotFound(doc_id)
    meta["title"] = title.strip() or meta["title"]
    meta["updated_at"] = datetime.now(UTC).isoformat()
    save_meta(meta)
    logger.info("Document renamed: id=%s", doc_id)
    return _meta_to_document(meta)


def delete_document(doc_id: str) -> None:
    """Purge a single document's pages, embeddings and meta, then rebuild the
    corpus index from what remains. Scoped to this document's prefixes only —
    never a bucket-wide wipe."""
    validate_doc_id(doc_id)
    if not load_meta(doc_id):
        raise DocumentNotFound(doc_id)
    store.delete_prefix(f"{PAGES_PREFIX}{doc_id}/")
    store.delete_prefix(f"{EMBED_PREFIX}{doc_id}/")
    store.delete_prefix(f"{DOCS_PREFIX}{doc_id}/")
    logger.info("Document deleted: id=%s", doc_id)
    # Local import breaks the documents<->ingest import cycle.
    from app.service.ingest import rebuild_index

    rebuild_index()


def corpus_stats() -> CorpusStats:
    """Dashboard rollup: doc/page counts plus the write-amplification headline
    (page-image bytes vs embedding bytes) and the FAISS index size."""
    documents = list_documents()
    total_pages = sum(d.page_count for d in documents)
    page_bytes = sum(d.page_bytes for d in documents)
    embedding_bytes = sum(d.embedding_bytes for d in documents)
    indexed = sum(1 for d in documents if d.status == "indexed")
    index_bytes = sum(obj["Size"] for obj in store.list_prefix(INDEX_PREFIX))
    return CorpusStats(
        documents=len(documents),
        indexed_documents=indexed,
        total_pages=total_pages,
        page_bytes=page_bytes,
        page_bytes_human=humanize_bytes(page_bytes),
        embedding_bytes=embedding_bytes,
        embedding_bytes_human=humanize_bytes(embedding_bytes),
        index_bytes=index_bytes,
        index_bytes_human=humanize_bytes(index_bytes),
    )
