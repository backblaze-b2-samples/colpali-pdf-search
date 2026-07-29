"""Real FAISS MaxSim tests with synthetic (not model-generated) vectors.

The ColPali model is never invoked here — these exercise the index math only:
building a flat-IP index over per-page patch vectors and MaxSim-ranking a
multi-vector query. numpy + faiss-cpu are real dependencies of the sample.
"""

import numpy as np

from app.repo.faiss_index import PageVectors, build_index, search


def _unit(vecs: np.ndarray) -> np.ndarray:
    vecs = vecs.astype("float32")
    norms = np.linalg.norm(vecs, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def test_build_and_search_ranks_aligned_page_first():
    dim = 8
    # Page A patches point mostly along axis 0; page B along axis 1.
    page_a = _unit(np.eye(dim)[[0, 0, 0]] + 0.01)
    page_b = _unit(np.eye(dim)[[1, 1, 1]] + 0.01)
    pages = [
        PageVectors(doc_id="a" * 32, page=1, vectors=page_a),
        PageVectors(doc_id="b" * 32, page=1, vectors=page_b),
    ]
    index_bytes, mapping = build_index(pages)
    assert mapping["dim"] == dim
    assert len(mapping["rows"]) == 6

    # Query aligned with axis 0 -> page A wins.
    query = _unit(np.eye(dim)[[0, 0]])
    ranked = search(index_bytes, mapping, query, top_k=2)
    assert ranked[0][0] == "a" * 32
    assert ranked[0][2] >= ranked[1][2]


def test_search_empty_index_returns_empty():
    assert search(b"", {"dim": 8, "rows": []}, np.zeros((2, 8), dtype="float32")) == []


def test_build_index_rejects_no_pages():
    import pytest

    with pytest.raises(ValueError):
        build_index([])
