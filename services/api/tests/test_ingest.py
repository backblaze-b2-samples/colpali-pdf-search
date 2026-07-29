"""Ingest pipeline tests. PDF rendering, the ColPali model, and the B2 store are
all mocked, so no weights are downloaded and no bytes leave the process. The
real render/model/index code paths are exercised by their own unit tests
(test_pdf_render, test_faiss_index) and by the verify step end-to-end."""

import numpy as np
import pytest

from app.service import ingest


@pytest.fixture
def mocked(monkeypatch):
    puts: dict[str, int] = {}

    def put_bytes(key: str, data: bytes, content_type: str) -> int:
        puts[key] = len(data)
        return len(data)

    monkeypatch.setattr(ingest.store, "put_bytes", put_bytes)
    monkeypatch.setattr(ingest, "save_meta", lambda meta: None)
    monkeypatch.setattr(ingest, "render_pdf_to_pngs", lambda b, dpi: [b"png1", b"png2png2"])
    return puts


def test_create_document_renders_and_stores(mocked):
    doc = ingest.create_document(
        b"%PDF-1.4 fake", title="Deck", dpi=150, model="vidore/colpali-v1.2"
    )
    assert doc.page_count == 2
    assert doc.status == "rendered"
    assert doc.page_bytes == len(b"png1") + len(b"png2png2")
    assert any(k.endswith("/1.png") for k in mocked)


def test_create_document_rejects_non_pdf(mocked):
    with pytest.raises(ingest.IngestError):
        ingest.create_document(b"GIF89a", title="x", dpi=150, model="vidore/colpali-v1.2")


def test_run_indexing_embeds_and_marks_indexed(monkeypatch, mocked):
    meta = {
        "id": "a" * 32,
        "title": "Deck",
        "page_count": 2,
        "dpi": 150,
        "model": "vidore/colpali-v1.2",
        "status": "rendered",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "page_bytes": 12,
        "embedding_bytes": 0,
    }
    saved: list[dict] = []
    monkeypatch.setattr(ingest, "load_meta", lambda doc_id: dict(meta))
    # Capture every persisted snapshot so we can assert progress is flushed as
    # indexing advances (the no-op save_meta from `mocked` is replaced here).
    monkeypatch.setattr(ingest, "save_meta", lambda m: saved.append(dict(m)))
    monkeypatch.setattr(
        ingest.store,
        "list_prefix",
        lambda prefix: [{"Key": f"pages/{'a' * 32}/{n}.png", "Size": 6} for n in (1, 2)],
    )
    monkeypatch.setattr(ingest.store, "get_object_bytes", lambda key: b"pngbytes")
    monkeypatch.setattr(
        ingest.colpali,
        "embed_images",
        lambda images, model_name=None: [np.ones((3, 8), dtype="float32") for _ in images],
    )
    monkeypatch.setattr(ingest, "rebuild_index", lambda: None)

    doc = ingest.run_indexing("a" * 32)
    assert doc.status == "indexed"
    assert doc.embedding_bytes > 0
    assert doc.pages_indexed == 2

    # status="indexing" (pages_indexed=0) is flushed BEFORE any embedding so a
    # mid-index reload observes an in-progress doc, not a re-runnable one.
    assert saved[0]["status"] == "indexing"
    assert saved[0]["pages_indexed"] == 0
    # The counter advances determinately per page and never regresses.
    progress = [s["pages_indexed"] for s in saved]
    assert progress == sorted(progress)
    assert 1 in progress and 2 in progress
    # The final persisted snapshot marks the doc indexed at full progress.
    assert saved[-1]["status"] == "indexed"
    assert saved[-1]["pages_indexed"] == 2


def test_run_indexing_missing_document(monkeypatch):
    monkeypatch.setattr(ingest, "load_meta", lambda doc_id: None)
    with pytest.raises(ingest.DocumentNotFound):
        ingest.run_indexing("a" * 32)
