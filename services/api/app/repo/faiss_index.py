"""FAISS index over ColPali page-patch vectors, with MaxSim late interaction.

Every page contributes many patch vectors. We flatten all patches from all
pages into one `IndexFlatIP` (inner product == cosine, since vectors are
L2-normalized in repo/colpali.py) and keep a row->(doc_id, page) mapping. At
query time we score with MaxSim: for each query token take the best matching
patch per page, then sum those maxima across query tokens. The index and its
mapping are serialized to bytes and stored in B2 (index/index.faiss,
index/mapping.json), so the searchable corpus lives entirely in object storage.

faiss is imported lazily so importing the app never needs the native wheel.
"""

from collections import defaultdict
from dataclasses import dataclass

import numpy as np


@dataclass
class PageVectors:
    doc_id: str
    page: int
    vectors: np.ndarray  # [num_patches, dim], float32, L2-normalized


def _faiss():
    """Import faiss lazily and cap it to a single OpenMP thread.

    faiss-cpu and PyTorch (loaded via repo/colpali.py) each bundle their own
    OpenMP runtime. With both live in one process, a multi-threaded faiss
    parallel region aborts or segfaults on macOS ("OMP: Error #15 / #179").
    Together with KMP_DUPLICATE_LIB_OK=TRUE (set in repo/__init__.py), running
    faiss single-threaded keeps search stable while leaving torch
    multithreaded for fast embedding. omp_set_num_threads is process-global and
    idempotent, so calling it on every import is cheap and safe. Flat-index
    search over a demo corpus does not benefit meaningfully from faiss threads.
    """
    import faiss

    faiss.omp_set_num_threads(1)
    return faiss


def build_index(pages: list[PageVectors]) -> tuple[bytes, dict]:
    """Build a flat IP index over every page's patch vectors.

    Returns (serialized_index_bytes, mapping) where mapping is
    {"dim": int, "rows": [{"doc_id", "page"}, ...]} aligned to index rows.
    Raises ValueError when there is nothing to index.
    """
    faiss = _faiss()

    if not pages:
        raise ValueError("Cannot build an index with no pages")

    dim = int(pages[0].vectors.shape[1])
    matrices: list[np.ndarray] = []
    rows: list[dict] = []
    for pv in pages:
        vecs = np.ascontiguousarray(pv.vectors, dtype="float32")
        matrices.append(vecs)
        rows.extend({"doc_id": pv.doc_id, "page": pv.page} for _ in range(vecs.shape[0]))

    all_vectors = np.vstack(matrices).astype("float32")
    index = faiss.IndexFlatIP(dim)
    index.add(all_vectors)

    serialized = faiss.serialize_index(index)
    return np.asarray(serialized, dtype="uint8").tobytes(), {"dim": dim, "rows": rows}


def search(
    index_bytes: bytes,
    mapping: dict,
    query_vectors: np.ndarray,
    top_k: int = 10,
) -> list[tuple[str, int, float]]:
    """MaxSim-rank pages for a multi-vector query.

    Returns [(doc_id, page, score), ...] sorted by descending score.
    """
    faiss = _faiss()

    rows = mapping.get("rows", [])
    if not rows or index_bytes == b"":
        return []

    index = faiss.deserialize_index(np.frombuffer(index_bytes, dtype="uint8"))
    query = np.ascontiguousarray(query_vectors, dtype="float32")
    if query.ndim != 2 or index.ntotal == 0:
        return []

    # Retrieve a generous set of patches per query token so each candidate page
    # is very likely represented for the per-token max (ANN MaxSim).
    fetch = min(index.ntotal, max(top_k * 50, 200))
    scores, ids = index.search(query, fetch)

    # page -> {token_index: best score seen for that token on this page}
    page_token_max: dict[tuple[str, int], dict[int, float]] = defaultdict(dict)
    num_tokens = query.shape[0]
    for token in range(num_tokens):
        for rank in range(fetch):
            row = int(ids[token, rank])
            if row < 0:
                continue
            entry = rows[row]
            key = (entry["doc_id"], entry["page"])
            score = float(scores[token, rank])
            best = page_token_max[key].get(token)
            if best is None or score > best:
                page_token_max[key][token] = score

    ranked = [
        (doc_id, page, float(sum(token_scores.values())))
        for (doc_id, page), token_scores in page_token_max.items()
    ]
    ranked.sort(key=lambda item: item[2], reverse=True)
    return ranked[:top_k]
