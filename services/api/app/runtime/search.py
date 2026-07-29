"""Visual search route. Embedding the query loads the ColPali model, so the
work is offloaded to the threadpool."""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.service.search import SearchError, search
from app.types import SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Natural-language visual query"),
    top_k: int = Query(10, ge=1, le=50),
):
    try:
        return await run_in_threadpool(search, q, top_k)
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None
