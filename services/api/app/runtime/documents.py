"""Document routes: ingest (create), list/read, rename (edit), delete, and the
`run indexing` action. Handlers stay thin — validation and orchestration live
in service/. Blocking B2 and model work is offloaded to the threadpool so a
long ingest never stalls the event loop.
"""

import logging

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.service.documents import (
    DocumentNotFound,
    InvalidDocumentId,
    corpus_stats,
    delete_document,
    get_document_detail,
    list_documents,
    rename_document,
)
from app.service.ingest import (
    ALLOWED_DPI,
    ALLOWED_MODELS,
    IngestError,
    create_document,
    run_indexing,
)
from app.types import (
    CorpusStats,
    Document,
    DocumentDetail,
    DocumentRenameRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# SECURITY: like the file routes, these are intentionally unauthenticated and
# corpus-wide (single-tenant demo). A multi-tenant clone must add auth to every
# route AND scope reads/writes to the caller's own documents.

MAX_PDF_BYTES = 100 * 1024 * 1024


@router.post("/documents", response_model=Document)
async def ingest_document_endpoint(
    file: UploadFile,
    title: str = Form(""),
    dpi: int = Form(settings.render_dpi),
    model: str = Form(settings.colpali_model),
):
    if dpi not in ALLOWED_DPI:
        raise HTTPException(status_code=400, detail=f"dpi must be one of {ALLOWED_DPI}")
    if model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Unsupported model")

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="PDF too large")
        chunks.append(chunk)
    pdf_bytes = b"".join(chunks)

    try:
        return await run_in_threadpool(
            create_document, pdf_bytes=pdf_bytes, title=title, dpi=dpi, model=model
        )
    except IngestError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None


@router.get("/documents", response_model=list[Document])
def list_documents_endpoint():
    return list_documents()


@router.get("/documents/stats", response_model=CorpusStats)
def corpus_stats_endpoint():
    return corpus_stats()


@router.get("/documents/{doc_id}", response_model=DocumentDetail)
def get_document_endpoint(doc_id: str):
    try:
        return get_document_detail(doc_id)
    except InvalidDocumentId as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=e.detail) from None


@router.patch("/documents/{doc_id}", response_model=Document)
def rename_document_endpoint(doc_id: str, body: DocumentRenameRequest):
    try:
        return rename_document(doc_id, body.title)
    except InvalidDocumentId as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=e.detail) from None


@router.delete("/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    try:
        await run_in_threadpool(delete_document, doc_id)
    except InvalidDocumentId as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=e.detail) from None
    return {"deleted": True, "id": doc_id}


@router.post("/documents/{doc_id}/index", response_model=Document)
async def index_document_endpoint(doc_id: str):
    try:
        return await run_in_threadpool(run_indexing, doc_id)
    except InvalidDocumentId as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=e.detail) from None
    except IngestError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None
