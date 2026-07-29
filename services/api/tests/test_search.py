"""Visual search service tests. The store, the ColPali query encoder, and the
FAISS search are mocked; the MaxSim math itself is covered by
test_faiss_index."""

import numpy as np
import pytest

from app.service import documents as docsvc
from app.service import search as searchsvc
from app.types import Document

DOC_A = "a" * 32


def _document() -> Document:
    return Document(
        id=DOC_A,
        title="Doc A",
        page_count=3,
        dpi=150,
        model="vidore/colpali-v1.2",
        status="indexed",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def test_empty_query_raises():
    with pytest.raises(searchsvc.SearchError):
        searchsvc.search("   ")


def test_no_index_returns_empty(monkeypatch):
    monkeypatch.setattr(searchsvc.store, "read_json", lambda key: None)
    monkeypatch.setattr(searchsvc.store, "list_prefix", lambda prefix: [])
    result = searchsvc.search("anything")
    assert result.hits == []


def test_search_returns_ranked_hits(monkeypatch):
    monkeypatch.setattr(
        searchsvc.store, "read_json", lambda key: {"dim": 8, "rows": [{"doc_id": DOC_A, "page": 2}]}
    )
    monkeypatch.setattr(searchsvc.store, "list_prefix", lambda prefix: [{"Key": docsvc.INDEX_KEY}])
    monkeypatch.setattr(searchsvc.store, "get_object_bytes", lambda key: b"indexbytes")
    monkeypatch.setattr(searchsvc.colpali, "embed_query", lambda text, model_name=None: np.ones((2, 8), dtype="float32"))
    monkeypatch.setattr(searchsvc.faiss_index, "search", lambda *a, **k: [(DOC_A, 2, 0.87)])
    monkeypatch.setattr(searchsvc, "list_documents", lambda: [_document()])
    monkeypatch.setattr(searchsvc.store, "presign_get", lambda key, **kw: f"https://b2/{key}")

    result = searchsvc.search("revenue waterfall chart", top_k=5)
    assert len(result.hits) == 1
    hit = result.hits[0]
    assert hit.doc_id == DOC_A
    assert hit.page == 2
    assert hit.title == "Doc A"
    assert hit.url.endswith("pages/" + DOC_A + "/2.png")
