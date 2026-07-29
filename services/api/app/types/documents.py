from datetime import datetime

from pydantic import BaseModel

# Document lifecycle status.
#   rendered -> PDF pages have been rasterized to PNGs and stored in B2.
#   indexing -> ColPali embedding is in progress; `pages_indexed` advances from
#               0 to `page_count` as each page is embedded (persisted so a
#               reload/poll can observe progress).
#   indexed  -> pages have been embedded with ColPali and folded into the
#               FAISS index; the document is searchable.
DocumentStatus = str  # "rendered" | "indexing" | "indexed"


class Document(BaseModel):
    """Summary record for one ingested PDF (from documents/<id>/meta.json)."""

    id: str
    title: str
    page_count: int
    dpi: int
    model: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    # Write-amplification headline: raw page-image bytes vs embedding bytes.
    page_bytes: int = 0
    embedding_bytes: int = 0
    # Pages embedded so far while status == "indexing" (0..page_count). Drives
    # determinate progress in the UI; 0 for rendered docs and reaches
    # page_count when indexing completes.
    pages_indexed: int = 0
    # Presigned URL to page 1 (for library thumbnails). Not persisted in
    # meta.json; populated on read.
    thumbnail_url: str | None = None


class DocumentPage(BaseModel):
    """One rendered page with a short-lived presigned URL to its PNG in B2."""

    page: int
    key: str
    url: str


class DocumentDetail(Document):
    """Full document view: the summary plus streamable page images."""

    pages: list[DocumentPage] = []


class DocumentRenameRequest(BaseModel):
    title: str


class CorpusStats(BaseModel):
    """Dashboard rollup across every ingested document."""

    documents: int
    indexed_documents: int
    total_pages: int
    page_bytes: int
    page_bytes_human: str
    embedding_bytes: int
    embedding_bytes_human: str
    index_bytes: int
    index_bytes_human: str
