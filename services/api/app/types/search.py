from pydantic import BaseModel


class SearchHit(BaseModel):
    """A single page retrieved for a visual query, with its MaxSim score."""

    doc_id: str
    title: str
    page: int
    score: float
    key: str
    url: str


class SearchResponse(BaseModel):
    query: str
    top_k: int
    hits: list[SearchHit]
