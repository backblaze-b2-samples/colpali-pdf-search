"""Document service tests. The B2 object store is mocked so these stay
hermetic — no boto3, no network, no model."""

import pytest

from app.service import documents as docsvc

DOC_A = "a" * 32
DOC_B = "b" * 32


def _meta(doc_id: str, title: str, status: str = "indexed", pages: int = 2) -> dict:
    return {
        "id": doc_id,
        "title": title,
        "page_count": pages,
        "dpi": 150,
        "model": "vidore/colpali-v1.2",
        "status": status,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "page_bytes": 1000,
        "embedding_bytes": 2000,
    }


@pytest.fixture
def store(monkeypatch):
    """A tiny in-memory stand-in for repo.store, wired into the service."""
    metas = {DOC_A: _meta(DOC_A, "Doc A"), DOC_B: _meta(DOC_B, "Doc B", "rendered")}
    saved: dict = {}

    def list_prefix(prefix: str):
        if prefix == docsvc.DOCS_PREFIX:
            return [{"Key": f"documents/{d}/meta.json", "Size": 100} for d in metas]
        if prefix == docsvc.INDEX_PREFIX:
            return [{"Key": "index/index.faiss", "Size": 4096}]
        if prefix.startswith(docsvc.PAGES_PREFIX):
            doc_id = prefix.split("/")[1]
            return [
                {"Key": f"pages/{doc_id}/{n}.png", "Size": 500}
                for n in range(1, metas[doc_id]["page_count"] + 1)
            ]
        return []

    def read_json(key: str):
        if key.startswith("documents/"):
            return metas.get(key.split("/")[1])
        return None

    def write_json(key: str, payload: dict):
        saved[key] = payload
        metas[payload["id"]] = payload

    monkeypatch.setattr(docsvc.store, "list_prefix", list_prefix)
    monkeypatch.setattr(docsvc.store, "read_json", read_json)
    monkeypatch.setattr(docsvc.store, "write_json", write_json)
    monkeypatch.setattr(docsvc.store, "presign_get", lambda key, **kw: f"https://b2/{key}")
    return {"metas": metas, "saved": saved}


def test_list_documents(store):
    docs = docsvc.list_documents()
    assert {d.id for d in docs} == {DOC_A, DOC_B}
    assert all(d.thumbnail_url and d.thumbnail_url.endswith("/1.png") for d in docs)


def test_get_document(store):
    doc = docsvc.get_document(DOC_A)
    assert doc.title == "Doc A"
    assert doc.status == "indexed"


def test_invalid_doc_id_raises():
    with pytest.raises(docsvc.InvalidDocumentId):
        docsvc.get_document("not-a-valid-id")


def test_missing_document_raises(store, monkeypatch):
    monkeypatch.setattr(docsvc.store, "read_json", lambda key: None)
    with pytest.raises(docsvc.DocumentNotFound):
        docsvc.get_document(DOC_A)


def test_rename_document(store):
    updated = docsvc.rename_document(DOC_A, "Renamed")
    assert updated.title == "Renamed"
    assert store["metas"][DOC_A]["title"] == "Renamed"


def test_corpus_stats(store):
    stats = docsvc.corpus_stats()
    assert stats.documents == 2
    assert stats.indexed_documents == 1
    assert stats.total_pages == 4
    assert stats.page_bytes == 2000
    assert stats.embedding_bytes == 4000
    assert stats.index_bytes == 4096


def test_get_document_detail_lists_pages(store):
    detail = docsvc.get_document_detail(DOC_A)
    assert [p.page for p in detail.pages] == [1, 2]
    assert all(p.url.startswith("https://b2/") for p in detail.pages)
