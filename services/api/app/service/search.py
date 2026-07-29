"""Visual search: embed a text query with ColPali, MaxSim-rank pages against
the FAISS index stored in B2, and return the matching page images (streamed
from B2 via presigned URLs) with relevance scores.
"""

import logging

from app.config import settings
from app.repo import colpali, faiss_index, store
from app.service.documents import (
    INDEX_KEY,
    MAPPING_KEY,
    PAGES_PREFIX,
    list_documents,
)
from app.types import SearchHit, SearchResponse

logger = logging.getLogger(__name__)


class SearchError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def search(query: str, top_k: int | None = None) -> SearchResponse:
    """Run a visual query against the indexed corpus."""
    query = query.strip()
    if not query:
        raise SearchError("Query must not be empty")
    top_k = top_k or settings.search_top_k

    mapping = store.read_json(MAPPING_KEY)
    index_meta = store.list_prefix(INDEX_KEY)
    if not mapping or not index_meta:
        # No corpus indexed yet — return an empty result set, not an error.
        return SearchResponse(query=query, top_k=top_k, hits=[])

    index_bytes = store.get_object_bytes(INDEX_KEY)
    query_vectors = colpali.embed_query(query)
    ranked = faiss_index.search(index_bytes, mapping, query_vectors, top_k=top_k)

    titles = {doc.id: doc.title for doc in list_documents()}
    hits: list[SearchHit] = []
    for doc_id, page, score in ranked:
        key = f"{PAGES_PREFIX}{doc_id}/{page}.png"
        hits.append(
            SearchHit(
                doc_id=doc_id,
                title=titles.get(doc_id, doc_id),
                page=page,
                score=round(score, 4),
                key=key,
                url=store.presign_get(key),
            )
        )
    logger.info("Visual search: q_len=%d hits=%d", len(query), len(hits))
    return SearchResponse(query=query, top_k=top_k, hits=hits)
