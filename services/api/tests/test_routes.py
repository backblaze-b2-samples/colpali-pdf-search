"""HTTP-level tests for the document and search routes. Validation paths need
no B2; the "missing document" and "empty search" paths mock the store."""

from app.service import documents as docsvc
from app.service import search as searchsvc

PDF = ("x.pdf", b"%PDF-1.4 fake", "application/pdf")


async def test_ingest_rejects_bad_dpi(client):
    resp = await client.post(
        "/documents",
        files={"file": PDF},
        data={"dpi": "999", "model": "vidore/colpali-v1.2", "title": "t"},
    )
    assert resp.status_code == 400


async def test_ingest_rejects_bad_model(client):
    resp = await client.post(
        "/documents",
        files={"file": PDF},
        data={"dpi": "150", "model": "not-a-model", "title": "t"},
    )
    assert resp.status_code == 400


async def test_get_document_invalid_id(client):
    resp = await client.get("/documents/not-valid")
    assert resp.status_code == 400


async def test_get_document_not_found(client, monkeypatch):
    monkeypatch.setattr(docsvc.store, "read_json", lambda key: None)
    resp = await client.get(f"/documents/{'a' * 32}")
    assert resp.status_code == 404


async def test_search_requires_query(client):
    resp = await client.get("/search?q=")
    assert resp.status_code == 422


async def test_search_empty_corpus(client, monkeypatch):
    monkeypatch.setattr(searchsvc.store, "read_json", lambda key: None)
    monkeypatch.setattr(searchsvc.store, "list_prefix", lambda prefix: [])
    resp = await client.get("/search?q=hello")
    assert resp.status_code == 200
    assert resp.json()["hits"] == []
